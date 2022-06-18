import { HttpClient } from '@angular/common/http';
import { Component, ComponentFactoryResolver, OnInit } from '@angular/core';
import { of } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { NzMessageService } from 'ng-zorro-antd/message';


@Component({
  selector: 'collection',
  templateUrl: './collection.component.html',
  styleUrls: [ './collection.component.css' ]
})

export class CollectionComponent implements OnInit {
  initLoading = true;
  loadingMore = false;
  data: any[] = [];
  list: any[] = [];
  listSelected: any[] = [];
  gridStyle = {
    width: '25%',
    textAlign: 'center'
  };
  searchString: string = "";
  // DataUrl = 'https://daolytics.live/api/searchstring?';
  DataUrl = 'http://localhost:4200/api/searchstring?';
  DataFetchMetricsUrl = 'http://localhost:4200/api/metrics?';
  constructor(private http: HttpClient, private msg: NzMessageService) {}

  ngOnInit(): void {
  }

  getData(callback: (res: any) => void, searchString: string): void {
    this.http
      .get(this.DataUrl.concat("searchstring=",searchString))
      .pipe(catchError(() => of({ res: [] })))
      .subscribe((res: any) => callback(res));
    console.log(this.DataUrl.concat("searchstring=",searchString));
  }

  getMetrics(callback: (res: any) => void, poapList: string): void {
    this.http
      .get(this.DataUrl.concat("metrics=", poapList))
      .pipe(catchError(() => of({ res: [] })))
      .subscribe((res: any) => callback(res));
    console.log(this.DataUrl.concat("metrics=",poapList));
  }

  onLoadMore(): void {
    this.loadingMore = true;
    this.http
      .get(this.DataUrl)
      .pipe(catchError(() => of({ data: [] })))
      .subscribe((res: any) => {
        this.data = this.data.concat(res.data);
        this.list = [...this.data];
        this.loadingMore = false;
      });
  }

  edit(item: any): void {
    this.msg.success(item.email);
  }

  onSearch(searchString: string): void {
    this.getMetrics((res: any) => {
      console.log(res)
      this.data = res;
      this.list = res;
      console.log(this.data);
      console.log(this.list);
      this.initLoading = false;
      this.list.forEach((number, index) => {
        this.list[index] = { ...this.list[index], selected: false};
    });
    }, searchString);
  }

  onGenerateClick(): void {
    var poapList = "";
    for (var index in this.listSelected) {
          poapList = poapList + this.listSelected[index].id;
    }
    this.getData((res: any) => {
      console.log(res)
      this.data = res;
      this.list = res;
      console.log(this.data);
      console.log(this.list);
      this.initLoading = false;
    }, poapList);
  }

  onSelectionClick(item: any){
    item.selected = !item.selected;
    if (item.selected)
    {
      this.listSelected.push(item)
    }
    else
    {
      var index = this.listSelected.indexOf(item)
      this.listSelected.splice(index,1)
    }
  }

  onSecondarySelectionClick(item: any){
    var index = this.listSelected.indexOf(item);
    this.listSelected[index].selected = !this.listSelected[index].selected;
    this.listSelected.splice(index,1)
  }

}