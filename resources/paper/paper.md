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
  - name: Michael Fitzmaurice
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

`PAM` is an activity modelling tool. It can be used for creating, modifying or modelling synthetic populations of agents and their activity sequences. Where activity sequences represent individual agent actions and movements.

Modelling how a population of people will behave in some future scenario is an important tool in policy, operational, and infrastructure decision making.
In the transport domain, this might be predicting how many people will buy an electric vehicle so that future energy demand can be planned, or predicting how many people will use a new train station so that a new rail line can be funded.

Activity modelling is a growing paradigm used for these models, in which individuals are explicitly represented and their movements are based on predicting sequences of activities connected by trips [@TRB-primer].
Each activity is geolocated and has a type or purpose, such as "work". Figure \ref{fig:Example activity sequences} shows illustrative activity sequence outputs from an activity model.
This is a key shift from more simplified approaches and can be used to potentially create more useful and more accurate predictions [@Rasouli].

Activity modelling is also a key component of agent-based modelling approaches such as MATSim [@MATSim:2016].

`PAM` provides functionality for these applications, including working with MATSim.

![Example activity sequences for persons A, B and C. Connected coloured blocks represent activities that take place at specific locations. Note, for example, that persons A and B share the same workplace. Connecting lines represent travel between these locations.\label{fig:Example activity sequences}](../example-activity-plans.png)

# Existing tooling review

In the transport domain, we are aware of two open-source activity-based transport modeling tools. The first is ActivitySim [@ActivitySim], an established framework of model components developed and extensively applied in the United States. Although there is some flexibility within the underlying API, the framework is highly opinionated and relatively inaccessible without training. The second is Eqasim [@Eqasim], a newer project for creating scenarios for MATSim. The project provides a pipeline of various Python and java-based tools for generating MATSim scenarios using an activity-based modeling approach. There is potential to reuse this framework beyond MATSim, but users require significant MATSim experience to do so.

# Statement of need

`PAM` is a Python package providing a pythonic API for creating and/or working with activity-based synthetic populations. `PAM` provides read/write functionality for common data formats, such as travel diaries and full support for MATSim formats.

`PAM` is intended for use by those wanting to (i) build their own activity model, (ii) modify existing synthetic populations to create new scenarios, and (iii) work with the agent-based modelling tool MATSim.

`PAM` provides an accessible and flexible tooling for researchers and practitioners to experiment with activity modelling approaches and quickly build synthetic populations to use in downstream applications, such as simulations.

# Design

The core `PAM` API provides intuitive objects, representing populations, households, persons, vehicles, plans, activities and trips. These are represented in memory as trees, such that a population is composed of households, household composed of persons and so on.

`PAM` builds common higher-level functionality on this core data structure, such as read/write operations, samplers, modifications and visualisation. `PAM` provides example notebooks of these applications as part of its documentation, and common features are exposed via a command-line interface.

The design of `PAM` will not be performant in some situations. Rather it focuses on accessibility and flexibility.

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