#!/usr/bin/env python

from distutils.core import setup

setup(
    name="fbpostscraper",
    version="0.01",
    description="Selenium-based scraper for public FB posts",
    author="Nel Ruigrok & Wouter van Atteveldt",
    author_email="nelruigrok@nieuwsmonitor.org",
    packages=["fbpostscraper"],
    include_package_data=False,
    keywords = ["Scraping"],
    classifiers=[
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scraping",
    ],
    install_requires=[
        "selenium",
        "amcatclient"
    ]
)