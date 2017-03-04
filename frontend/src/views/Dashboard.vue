<template>
  <div class="animated fadeIn">
    <div class="row">
      <div class="col-sm-6 col-lg-4">
        <div class="card card-inverse card-primary" v-on:click="getData">
          <div class="card-block pb-0">
            <h4 class="mb-0">{{stats.daily}}</h4>
            <p>Daily Spending</p>
          </div>
          <div class="chart-wrapper px-1" style="height:70px;">
            <card-line1-chart-example height="70"/>
          </div>
        </div>
      </div><!--/.col-->

      <div class="col-sm-6 col-lg-4">
        <div class="card card-inverse card-danger" v-on:click="getData">
          <div class="card-block pb-0">
            <h4 class="mb-0">{{stats.weekly}}</h4>
            <p>Weekly Spending</p>
          </div>
          <div class="chart-wrapper px-1" style="height:70px;">
            <card-bar-chart-example height="70"/>
          </div>
        </div>
      </div><!--/.col-->

      <div class="col-sm-6 col-lg-4">
        <div class="card card-inverse card-warning" v-on:click="getData">
          <div class="card-block pb-0">
            <h4 class="mb-0">{{stats.monthly}}</h4>
            <p>Monthly Spending</p>
          </div>
          <div class="chart-wrapper" style="height:70px;">
            <card-line3-chart-example height="70"/>
          </div>
        </div>
      </div><!--/.col-->

    </div><!--/.row-->

    <div class="card">
      <div class="card-block">
        <div class="row">
          <div class="col-sm-5">
            <h4 class="card-title mb-0">Spending last month</h4>
            <div class="small text-muted">Breakdown by day</div>
          </div><!--/.col-->
        </div><!--/.row-->
        <line-chart :chart-data="datacollection"
                 :height="400"
                 :options="{responsive: true, maintainAspectRatio: false,legend:{display:false}}"></line-chart>
      </div>
    </div><!--/.card-->

    <div class="row">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">
            Spending by Category
          </div>
          <div class="card-block">
            <div class="row">
              <doughnut-example :chart-data="pie_data"/>
            </div><!--/.row-->
          </div>
        </div>
      </div><!--/.col-->
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">
            Friends
          </div>
          <div class="card-block">
            <table class="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Waste Produced Today</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="friend in friend_data">
                  <td>{{friend.name}}</td>
                  <td>${{friend.spendings}}</td>
                  <td>
                    <span class="badge badge-danger" v-if="friend.mineIsGreater">Beating you</span>
                    <span class="badge badge-success" v-else>You're ahead</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <!--/.row-->
      </div>
    </div>
  </div><!--/.col-->
  </div><!--/.col-->
  </div>
</template>

<script>
import CardLine1ChartExample from './dashboard/CardLine1ChartExample'
import CardLine2ChartExample from './dashboard/CardLine2ChartExample'
import CardLine3ChartExample from './dashboard/CardLine3ChartExample'
import CardBarChartExample from './dashboard/CardBarChartExample'
import MainChartExample from './dashboard/MainChartExample'
import SocialBoxChartExample from './dashboard/SocialBoxChartExample'
import DoughnutExample from './charts/DoughnutExample'
import LineChart from './dashboard/LineChart.js'

import { dropdown } from 'vue-strap'

export default {
  name: 'dashboard',
  data(){
    return {
      uid: 0,
      stats: {
        daily: 111,
        monthly: 222,
        weekly: 333,
      },
      chartData: null,
      pulledData: null,
      datacollection:  {
        labels: [1],
        datasets: [
        {
          label: 'Data One',
          backgroundColor: '#f87979',
          data: [1]
        }, {
          label: 'Data One',
          backgroundColor: '#f87979',
          data: [1]
        }
        ]
      },
      pie_data: {
        labels: ['Lool', 'EmberJs', 'ReactJs', 'AngularJs', 'Vanilla'],
        datasets: [
        {
          backgroundColor: [
            '#41B883',
            '#E46651',
            '#00D8FF',
            '#DD1B16',
            '#7B1fA2',
            '#963BB8',
            '#303f9f',
            '689f38'
          ],
          data: [40, 20, 80, 10, 15]
        }
        ]
      },
      friend_data: [{name: "Fake person", mineIsGreater: true, spendings: 12}]
      
    }
  },
  components: {
    CardLine1ChartExample,
    CardLine2ChartExample,
    CardLine3ChartExample,
    CardBarChartExample,
    DoughnutExample,
    MainChartExample,
    LineChart,
    SocialBoxChartExample,
    dropdown
  },
  mounted: function(){
    this.uid = this.$route.params.uid
    console.log(this.$route.params)
    this.getData();
  }, 
  methods: {
    getRandomInt () {
      return Math.floor(Math.random() * (50 - 5 + 1)) + 5
    },
 
    getData(){
    //Get spending summary
    this.$http.get('http://localhost:5000/'+this.uid+'/spending_summary/').then(response => {
      this.stats.monthly = response.body.monthly;
    this.stats.daily = response.body.daily;
    this.stats.weekly = response.body.weekly;
    this.pulledData = response.body.per_day;

    const brandInfo = '#63c2de'
      this.datacollection = {
        labels: response.body.days,
        datasets: [
        {
          backgroundColor:brandInfo,
          borderColor: brandInfo,
          pointHoverBackgroundColor: '#fff',
          borderWidth: 2,
          data: response.body.per_day
        }
        ]
      }

    }, response => {
      console.log(response);
      // error callback
    });

    //Get the spending categories
    this.$http.get('http://localhost:5000/'+this.uid+'/category/week').then(response => {
      this.pie_data = {
        labels: Object.keys(response.body),
        datasets: [
        {
          backgroundColor: [
            '#41B883',
            '#E46651',
            '#00D8FF',
            '#DD1B16',
            '#7B1fA2',
            '#963BB8',
            '#303f9f',
            '689f38'
          ],
          data: Object.values(response.body)
        }
        ]
      }
    }, err => {});

    //Get your friends data
    this.$http.get('http://localhost:5000/'+this.uid+'/friends').then(response => {
      this.friend_data = response.body.friends
    }, err => {});


  }
  }
}
</script>
