# Personal Digital Dashboard

The motivation behind this project came about from me wanted to have a centralised place to view important information about myself instead of having to check various different apps. We spend so much time in our daily lives using 10+ systems for personal & social services via a tedious "pull" system with no simple aggregation. I felt this would be a good start to get a quick glance at how I am doing with progress on these services. 

By creating this dashboard to track my finances, fitness and investments I have consolidated roughly over 6 apps/websites into 1 including many banking and fitness apps. 

Made with Python 3, Dash/Flask, PostgreSQL and serveral API's and/or [Selenium](https://github.com/SeleniumHQ/selenium/tree/master/py)/[BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) to scrape my data when a public api isn't provided.

This repo also contains util scripts that automatically importing bank transactions to YNAB, aggregates statements from my email and sends weekly digests to me via cron jobs on a raspberry pi.

![alt text](https://i.imgur.com/8gu92qa.jpg "Logo Title Text 1")
![alt text](https://i.imgur.com/rSgHcDY.jpg "Logo Title Text 1")
![alt text](https://i.imgur.com/IQ53QRW.jpg "Logo Title Text 1")

Designed based on the mobile-first approach as I will mostly use it on mobile to quickly check my stats.

![alt text](https://i.imgur.com/HVZdPfD.jpg "Logo Title Text 1")


The theme also switches between light and dark based on the user's display settings

![alt text](https://i.imgur.com/TgFDKth.jpg "Logo Title Text 1")
![alt text](https://i.imgur.com/TYg2Qau.jpg "Logo Title Text 1")

## Key Notes

Used a 7 day moving average to analyze it weight loss/gain. ploting daily weight on an average curve smoothens out the daily fluctuations in weight. This has many benefits such as showing weight trends and lessens the daily fluctuations. I feel seeing an overall upward/downward trend based on your goal is much more inportant then individual points. Many factors can influence a weigh in such as how much extra water you retained last night because you ate something salty. Espically as I can currently trying alternative day fasting I'll natuarlly see big diferences in my fasted vs non-fasted weight-ins. A simply moving average helps show whether this approach is working. 
