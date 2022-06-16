import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit{

  isCollapsed = true;
  title = "Daolytics";

  constructor() { 
    this.isCollapsed = true;
    this.title = "Daolytics";
  }

  ngOnInit() {
  }

}
