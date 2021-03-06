// import components
import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { Title } from '@angular/platform-browser';
import { PropertiesService } from '../../services';

@Component({
  selector: 'app-footer',
  templateUrl: './footer.component.html',
  styleUrls: ['./footer.component.scss'],
  encapsulation: ViewEncapsulation.None
})

// Footer Component
export class FooterComponent implements OnInit {
  
  /**
   * constructor Footer Component
   */
  constructor(public properties: PropertiesService,
  			  private titleService: Title,
          private router: Router,
          private route:ActivatedRoute) {
    // console.log(this.route);
  	this.initToolName();
  }

  ngOnInit() {
  }

  /**
   * set title tool name
   * [initToolName description]
   */
  initToolName() {
    this.titleService.setTitle('Cloud Network Tools (powered by Aviatrix)');
  }

  /**
   * set Download link
   * [download description]
   */
  download(){
    if(this.properties.getCurerntToolName() == this.properties.AWS) {
      return this.properties.AWS_DOWNLOAD_URL;
    } else if(this.properties.getCurerntToolName() == this.properties.AZURE) {
      return this.properties.AZURE_DOWNLOAD_URL;
    } else {
      return this.properties.DOWNLOAD_URL;
    }
  }
}
