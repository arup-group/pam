---
title: 'PAM: Population Activity Modeller'
tags:
  - Python
  - Activity model
  - Synthetic population
  - MATSim
authors:
  - name: Fred Shone
    orcid: 0009-0008-1079-0081
    affiliation: 1 # (Multiple affiliations must be quoted)
  - name: Theodore Chatziioannou
    affiliation: 1
  - name: Bryn Pickering
    orcid: 0000-0003-4044-6587
    affiliation: 1
  - name: Kasia Kozlowska
    affiliation: 1
  - names: Michael Fitzmaurice
    affiliation: 1
affiliations:
 - name: Arup, City Modelling Lab
   index: 1
date: 12 September 2023
bibliography: paper.bib

# Optional fields if submitting to a AAS journal too, see this blog post:
# https://blog.joss.theoj.org/2018/12/a-new-collaboration-with-aas-publishing
# aas-doi: 10.3847/xxxxx <- update this with the DOI from AAS once you know it.
# aas-journal: Astrophysical Journal <- The name of the AAS journal.
---

# Summary

Modelling how a population of people will behave in some future scenario is an important tool in policy, operational, and infrastructure decision making.
In the transport domain, this might be predicting how many people will buy an electric vehicle so that future energy demand can be planned, or predicting how many people will use a new train station so that a new rail line can be funded.

Activity modelling is a growing paradigm used for these models, in which individuals are explicitly represented and their movements are based on predicting sequences of activities connected by trips [@TRB-primer].
Each activity is geolocated and has a type or purpose, such as "work".
This is a key shift from more simplified approaches and can be used to potentially create more useful and more accurate predictions [@Rasouli].

Activity modelling is also a key component of agent-based modelling approaches such as MATSim [@MATSim:2016].

![Example activity sequences.\label{fig:Example activity sequences}](../example-activity-plans.png)

# Statement of need

`PAM` is a python package providing a pythonic API for creating and/or working with activity-based synthetic populations. `PAM` provides read/write functionality for common data formats, such as travel diaries and full support for MATSim formats.
The `PAM` API allows users to create and/or manipulate activity sequences using intuitive objects and methods.
This allows researchers and practitioners to experiment with activity modelling approaches and quickly build synthetic populations to use in downstream applications, such as simulations.

`PAM` is intended for use by those wanting to (i) build their own activity model, (ii) modify existing synthetic populations to create new scenarios, and (iii) work with the agent-based modelling tool MATSim.
`PAM` provides example notebooks of these applications as part of its extensive documentation, and common features are exposed via a command-line interface.

# Development history

`PAM` was originally conceived and built at the start of the global COVID-19 pandemic, to allow for the assessment of change resulting from government quarantining and lock-down policies.
The project was originally called the `Pandemic Activity Modifier` and was applied to rapidly update existing transport demand models using `policies`, as described by [@Medium].
Updated transport demand could then be used for transport simulation using MATSim and virus transmission modelling using EpiSim [@Episim].

This application is still supported but `PAM` has since been generalised to provide broader application for activity modelling by both practitioners and researchers (e.g., [@Castro:2023]).
The project is now called the `Population Activity Modeller`.

# Acknowledgements

We acknowledge all past, present, and future contributions, including code, documentation, issues and feedback.
We also acknowledge funding and support from [Arup](https://www.arup.com/).

# References