# Hockey Analytics
In this repo, you will find my Jupyter Notebook files where I calculate and analyzed the data for both my blog as well as for the articles for the Bruins Stats Corner with<a href="https://blackngoldhockey.com/"> Black n Gold Hockey</a>.

## Goal Mapping
I built this <a href="https://goalmapping.streamlit.app/"> Streamlit app</a> to map and track goals throughout the NHL regular season. It's built on a python code developed in Jupyter Notebook that scrapes the NHL API daily. 

## Power Forwards
This <a href="https://tapetotapemk.substack.com/p/is-the-power-forward-a-thing-of-the"> blog post</a> idea was generated while I was writing and researching for <a href="https://blackngoldhockey.com/2023/08/bruins-stats-corner-jvr-the-contributor/"> this article. </a> The questions that prompted my exploration:
<ul>
 <li> What are the generally accepted characteristics of a Power Forwards? </li>
 <li> Is the popular notion "the Power Forward doesn't exist anymore" true? </li>
 <li> What is the "modern" Power Forward? </li>
 <li> How different is the "modern" Power Forward from the "classic" Power Forward? </li>
 <li> Who are some "players to watch" in their career, who might fit this new model? </li>
</ul>

## President's Trophy
I got this idea towards the end of the 2022-2023 NHL season; the Bruins were the best team in NHL history. Of course, the media began to hyper-focus on the idea of the "President's Trophy Curse". I get annoyed by things like that, so I wanted to see what the data says about teams who have won the President's Trophy and the Stanley Cup, as well as the season records of both (if they were not the same in a given season). It started out as a quick Google Sheets calculation, but I quickly realized I could get even more out of my questions by using Python. The result was <a href="https://tapetotapemk.substack.com/p/presidents-trophy-winners"> this blog post</a>. Like all the best exploration projects, my initial findings prompted even more questions:
<ul>
  <li> Is there a pattern when it comes to teams winning the President's Trophy and their playoff performance? </li>
  <li> If the top regular season team does not win the Cup, how does the winner's record compare? </li>
  <li> Are teams more likely to win a Stanley Cup within a certain amount of time after their President's Trophy win?</li>
</ul>

## Player Report Cards
Player report cards are fairly common out there for well-known hockey data scientists and hockey stats websites. Creating my own report card is something I have wanted to do for a while and I finally got around to starting the process. I spent time researching the stats that I felt were the most informative and interesting to use in evaluating hockey players. Current report cards lead readers to believe that they are completely objective (and to some extent they are), but they are so many ways to measure player performance, there is always going to be a level of subjectivity by the author. This is a long-term project that requires extensive thought around how it is organized and long-term testing over the course of a season.

My initial report card began as an evaluation of three Bruins Free Agents ahead of the 2023 NHL Free Agency. You can see more of my thought process and approach in <a href="https://tapetotapemk.substack.com/p/developing-a-player-report-card"> this blog post</a>. Some of my initial thoughts and questions:
<ul>
  <li> What are some interesting new stats I can introduce into the conversation?</li>
  <li> What are some current, commonly used stats in other report cards? </li>
  <li> How can I best evaluate a player's value to his team and his worth in the league?</li>
  <li> How do I handle players who are considered "elite" and meet those expectations compared to players who are second tier and exceed expectations?</li>
  <li> This lead me to realize that this report card system, just like handing out report cards in a classroom, should be used to evaluate a player as an individual first and as a player in the league second. For example, how a student performs in general and then how that student ranks in her graduating class. </li>
</ul>

## Player Usage
This is a favorite new metric for me. I first learned about it from an article by Dom Lusczyszczyn at The Athletic. I made a first pass at understanding it myself by attempting to replicate it back in 2023. In 2024, after letting it simmer on the back burner for a little while, I returned to my script with a fresh eye. I ended up changing quite a bit of how I was weighting the player usage values for players who were traded during the season. I then built off of that to determine if I could use player usage to predict anything and stumbled on an interesting discovery around how it relates to expected goals. I used this discovery to ask if the Bruins should <a href="https://tapetotapemk.substack.com/p/is-there-a-case-to-be-made-for-jake"> consider keeping Jake DeBrusk</a> before Free Agency.
<ul>
 <li> [2023 Script](https://github.com/kjchrz03/hockey/blob/main/Player%20Usage%202023.ipynb) </li>
 <li> [2024 Script](https://github.com/kjchrz03/hockey/blob/main/Player%20Usage%202024.ipynb) </li>
</ul>

## NHL API Webscraping

This is an example of [python scripting](https://github.com/kjchrz03/hockey/blob/main/NHLAPI%206.ipynb) to scrape the new NHL API

