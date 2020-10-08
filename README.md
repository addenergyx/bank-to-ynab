# Personal Digital Dashboard

The motivation behind this project came about from wanted to have a centralised place to view important information about myself instead of having to check various apps. We spend so much time in our daily lives using 10+ systems for personal & social services via a tedious "pull" system with no simple aggregation. I felt this would be an excellent start to get a glance at how I am progressing on these services. 

By creating this dashboard to track my finances, fitness and investments, I have consolidated roughly over six apps/websites into one, including many banking and fitness apps. 

Made with Python 3, Dash/Flask, PostgreSQL, several API's and [Selenium](https://github.com/SeleniumHQ/selenium/tree/master/py)/[BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) to scrape my data when a public API isn't provided.

This repo also contains util scripts that are automatically importing bank transactions to YNAB, aggregates statements from my email and sends weekly digests via cron jobs on a raspberry pi.

![Finances](https://i.imgur.com/8gu92qa.jpg)
![Body Fat](https://i.imgur.com/8vKcXgu.jpg)
![Weight](https://i.imgur.com/4rfBdha.jpg)
![Activity](https://i.imgur.com/xqHQkWE.jpg)
![Calories](https://i.imgur.com/sWnmab5.jpg)

Designed based on the mobile-first approach as I will mostly use it on mobile to quickly check my stats.

![alt text](https://i.imgur.com/HVZdPfD.jpg "Logo Title Text 1")


The theme also switches between light and dark based on the user's display settings

![alt text](https://i.imgur.com/TgFDKth.jpg "Logo Title Text 1")
![alt text](https://i.imgur.com/TYg2Qau.jpg "Logo Title Text 1")

## Key Notes

### Moving Average
Used a seven day moving average to analyze its weight loss/gain. Plotting daily weight on an average curve smoothens out the daily fluctuations in weight. This has many benefits, such as showing weight trends and lessens daily fluctuations. I feel that seeing an overall upward/downward trend based on your goal is much more critical than individual points. Many factors can influence a weigh-in such as how much extra water you retained last night because you ate something salty. Especially as I can currently trying alternative day fasting, I'll naturally see significant differences in my fasted vs non-fasted weight-ins. A simple moving average helps show whether this approach is working.

### Goals
Weight loss goals are based on advice from several fitness experts and journals 
