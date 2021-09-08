+++
image = "data_scheme_whiteboard.jpeg"
date = "2020-05-13"
title = "DS4SE"
type = "gallery"
+++

DS4SE, or Data Science for Software Engineering is an exploration into using natural language processing to auto-generate source code. For this project, I wrote a script with Wils McCreight to scrape github repositories in order to generate training data for the model. We ultimately scraped 5 million files each of python, java, C, and javascript. I then created a schema for the storage of these data artifacts, and created a mongo db to host these intermediate steps and an architecture for storing intermediate calculation steps / tokenization during model generation to allow for traceability of model generation. Find the repository (here)[https://github.com/WM-SEMERU/ds4se]. 