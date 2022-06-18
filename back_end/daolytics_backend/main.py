from flask import Flask, jsonify, request, send_file, render_template
import requests
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import collections
import networkx as nx
import io
import scipy as sp
from matplotlib.figure import Figure

matplotlib.use("Agg")

url = "https://api.poap.tech/paginated-events"
headers = {"Accept": "application/json"}

offset = 0
payload = {"offset": offset, "limit": "1000"}

response = requests.get(url, headers=headers, params=payload)
jsonStr = response.text
data = json.loads(jsonStr)
df = pd.json_normalize(data, record_path=["items"])

x = 0

while x < 35:

    offset = offset + 1000

    payload = {"offset": offset, "limit": "1000"}

    response = requests.get(url, headers=headers, params=payload)

    jsonStr = response.text

    data = json.loads(jsonStr)

    df = pd.concat(
        [df, (pd.json_normalize(data, record_path=["items"]))], ignore_index=True
    )

    x = x + 1

print(df.loc[1])

from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

# Select your transport with a defined url endpoint
transport = AIOHTTPTransport(
    url="https://api.thegraph.com/subgraphs/name/poap-xyz/poap-xdai"
)

# Create a GraphQL client using the defined transport
client = Client(transport=transport, fetch_schema_from_transport=True)

app = Flask(__name__)


@app.route("/incomes")
def get_incomes():
    return df.to_json()


@app.route("/api/searchstring")
def get_searchresult():
    searchString = request.args.get("searchstring")
    matchedPoaps = df.loc[df["name"].str.contains(searchString, case=False)]
    print(searchString)
    matchedPoaps = matchedPoaps.reset_index()
    return matchedPoaps.to_json(orient="records")


@app.route("/api/metrics")
def get_searchresult():
    ids = []
    metrics = request.args.get("metrics")
    metricsList = metrics.split(",")
    for index, row in enumerate(metricsList):
        ids.append(str(row["id"]))
        print(index)
        ##result = client.execute(query)
        ##data.append(result)
    qf = """
        query {
            tokens (first: 1000, where: {event_in: """

    ql = """
        }) {
        id,
        event {
            id
        },
        owner {
            id
        }
        }
    }"""
    query = str(qf.strip() + str(ids).strip().replace("'", '"') + ql.strip())
    print(qf.strip() + str(ids).strip().replace("'", '"') + ql.strip())
    query = gql(query)
    result = client.execute(query)
    print(result)
    resultdf = pd.json_normalize(result, record_path=["tokens"])
    aggregationdf = resultdf.copy(deep=True)
    while len(resultdf) != 0:
        qf = """
        query {
            tokens (first: 1000, where: {event_in: """

        qm = """
            , id_gt: """ + str(
            resultdf["id"].iloc[-1]
        )

        ql = """
            }) {
            id,
            event {
                id
            },
            owner {
                id
            }
            }
        }"""
        queryStr = str(
            qf.strip() + str(ids).strip().replace("'", '"') + qm.strip() + ql.strip()
        )
        query = gql(queryStr)
        result = client.execute(query)
        resultdf = pd.json_normalize(result, record_path=["tokens"])
        print("shape of result df", resultdf.shape)
        aggregationdf = pd.concat([aggregationdf, resultdf], ignore_index=True)

    aggregationdf.reset_index()
    print("number of records with duplicates", aggregationdf.shape)
    uniAggregationdf = aggregationdf.copy(deep=True)
    uniAggregationdf = uniAggregationdf.drop_duplicates(subset=["owner.id"])

    uniWal = list(uniAggregationdf["owner.id"])
    print(len(aggregationdf))
    conMat = np.zeros((len(aggregationdf), len(aggregationdf)))

    observations = aggregationdf[["owner.id", "event.id"]].to_records(index=False)

    eventLinks = {}
    for (walletAddress, eventId) in observations:
        # If this event have never been encoutered then create a new entry in links
        if not eventId in eventLinks.keys():
            eventLinks[eventId] = []
        eventLinks[eventId].append(walletAddress)

    # collect the wallet addresses
    walletAddresses = set([walletAd for (walletAd, eventId) in observations])

    # create a member link dictionary. This one link a mnbr to other mnbr linked to it.
    walletLinks = {walletAd: list() for walletAd in walletAddresses}
    walletLinksDict = {walletAd: dict() for walletAd in walletAddresses}

    for walletList in eventLinks.values():
        # add for each wallet all the wallets that attended the same event.
        for wallet in walletList:
            walletLinks[wallet] = walletLinks[wallet] + walletList

    print("line 187")

    for key in walletLinks.keys():
        walletLinksDict[key] = dict(
            zip(
                collections.Counter(walletLinks[key]).keys(),
                collections.Counter(walletLinks[key]).values(),
            )
        )

    print("line 190")

    matrix = []

    for i in range(len(walletLinks.keys())):
        matrix.append([0] * (len(walletLinks.keys())))

    print("line 197")

    for key in walletLinksDict.keys():
        for counterKey in walletLinksDict[key].keys():
            matrixkey1 = uniWal.index(key)
            matrixkey2 = uniWal.index(counterKey)
            if walletLinksDict[key][counterKey] != 0:
                matrix[matrixkey1][matrixkey2] = walletLinksDict[key][counterKey] / len(
                    ids
                )

    print(matrix)
    matrix = np.matrix(matrix)
    G = nx.from_numpy_matrix(matrix)
    nx.draw(G)
    print("size of matrix", len(matrix))
    print("size of dictionay", len(walletLinks.keys()))
    print("This is the size of values in events dictionary", len(eventLinks.values()))
    print("number of record without duplicates", uniAggregationdf.shape)
    print("number of record with duplicates", aggregationdf.shape)
    img = io.BytesIO()  # file-like object for the image
    print("line 227")
    plt.savefig("./static/assets/graph.png")
    img.seek(0)  # writing moved the cursor to the end of the file, reset
    print("line 231")
    plt.clf()  # clear pyplot
    # return send_file(img, mimetype="image/png")

    # matrix = np.tril(matrix)
    # histoMatrix = np.asarray(matrix).flatten()
    # histoMatrix = [histoMatrix != 0]

    # a = histoMatrix
    # plt.hist(a, bins=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    # plt.title("histogram")
    # imgHist = io.BytesIO()  # file-like object for the image
    # print("line 254")
    # plt.savefig(imgHist)
    # imgHist.seek(0)  # writing moved the cursor to the end of the file, reset
    # print("line 257")
    # plt.clf()  # clear pyplot

    # Embed the result in the html output.
    ##return f"<img src='data:image/png;base64,{data}'/>"

    return "./static/assets/graph.png"


@app.route("/incomes", methods=["POST"])
def add_income():
    return "", 204


@app.route("/", methods=["GET"])
def root():
    return render_template("index.html")  # Return index.html


if __name__ == "__main__":
    app.run()
