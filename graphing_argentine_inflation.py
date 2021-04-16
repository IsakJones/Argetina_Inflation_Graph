"""
DOCSTRING

Title: graphing_argentine_inflation
Author: Isak Jones
Date: 19 March 2020

May find std shading guide at: http://spatialminds.net/blog/moving-average/
"""

import re
import time
from datetime import datetime
from selenium import webdriver
from matplotlib import pyplot as plt

import numpy as np
import pandas as pd

class InflationProject(object):
    def __init__(
        self,
        website="http://www.bcra.gov.ar/PublicacionesEstadisticas/Principales_variables_datos.asp?serie=7931&detalle=Inflaci%F3n%20mensual%A0(variaci%F3n%20en%20%)",
        driverpath="/Users/isakjones/Desktop/Computer_Scienc3/Software/chromedriver",
        start_date="01012010",
        file="Argentine_Inflation.csv",
        whitespace_correction=re.compile(r"\s*(\S+)\s*"),
        decimal_correction=re.compile(r"\s*(\d+),(\d+)\s*"),
        width=3
        ):
        self.website = website
        self.driverpath = driverpath
        self.start_date = start_date
        self.file = file
        self.whitespace_correction = whitespace_correction
        self.decimal_correction = decimal_correction
        self.months = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec"
        ]
        self.colors = ["#990000",
                       "#1F6C05",
                       "#0D2356"]
        self.width = width
        self.plt_params()
        
    def plt_params(self):
        plt.rcParams["font.size"] = "16"
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = "Arial"
        plt.rcParams["legend.markerscale"] = 8
    
    def scraper(self):
    
        driver = webdriver.Chrome(self.driverpath)
        driver.get(self.website)
    
        start_date_input = driver.find_element_by_name("fecha_desde")
        start_date_input.send_keys(self.start_date)
        time.sleep(2)
        
        end_date_input = driver.find_element_by_name("fecha_hasta")
        end_date_input.send_keys(
            "".join(
                datetime.strptime(
                    end_date_input.get_attribute("max"),
                    "%Y-%m-%d"
                ).strftime(
                    "%m%d%Y"
                )
            )
        )
        time.sleep(2)
        
        button = driver.find_element_by_name("B1")
        button.click()
        
        data = {"Months" : self.months}
        table = driver.find_element_by_tag_name("table")
        rows = table.find_elements_by_tag_name("tbody")
        
        for row in rows:
            cells = row.find_elements_by_tag_name("td")
            year = datetime.strptime(
                self.whitespace_correction.sub(r"\1", cells[0].text),
                "%d/%m/%Y"
            ).year
            value = self.decimal_correction.sub(r"\1.\2", cells[1].text)
            try:
                data[year].append(value)
            except KeyError:
                data[year] = [value]
        
        pd.DataFrame(
            dict([ 
                  (k,pd.Series(v)) for k,v in data.items() 
            ])
        ).to_csv(self.file)
    
        time.sleep(1)
        driver.quit()
        return None
        

    def comparative_inflation(self, start_year=None, end_year=2013):
        
        if not start_year:
            start_year = int(self.start_date[-4:])
        
        df_inflation = self.corrected_df()
        df_old = df_inflation[
            [column for column in df_inflation if column <= end_year]
        ]
        old_values = np.array(
            [df_old[year] for year in df_old]
        )
        old_means = np.mean(old_values, axis=0)
        old_std = np.std(old_values)
        
        df_new = df_inflation[
            [column for column in df_inflation if column > end_year]
        ]
        SSRs = np.array([
            np.sum((old_means - np.array(df_new[year]))**2) for year in df_new
        ])
        maximum_SSR_years = [
            end_year+1+ind for ind in SSRs.argsort()[-2:][::-1]
        ]
        #Now plotting
        x_values = np.array(range(12)) + 1
        y_values = np.linspace(0, 7, num=15)
        percentages = [f"{num}%" for num in y_values]
        fig = plt.figure(figsize=(8,5))
        ax = fig.add_subplot(1, 1, 1)
        
        ax.plot(x_values, old_means, color=self.colors[0], alpha=0.9, label=f"{start_year}-{end_year}", linewidth=self.width-1)
        ax.fill_between(x_values, old_means - old_std, old_means + old_std, color=self.colors[0], alpha=0.4, label=None)
        
        for ind, year in enumerate(maximum_SSR_years):
            ax.plot(x_values, df_new[year], color=self.colors[ind+1], label=str(year), linewidth=self.width)
        
        ax.set_facecolor("#FFFFFF")
        plt.tight_layout()
        plt.legend()
        plt.grid(True)
        
        plt.title(f"Argentine Monthly Inflation, Average from {start_year}-{end_year}, Specific Plot from Most Deviant Years by SSR", fontsize=20)
        plt.xlabel("Month")
        plt.ylabel("Percentage Change")
        
        plt.xticks(x_values, labels=self.months, rotation="30")
        plt.yticks(y_values, labels=percentages, fontsize=14)
        plt.savefig("argentine_inflation_comparison.png")
        plt.show()
    
    def corrected_df(self):
        df_inflation = pd.read_csv(self.file)
        columns = df_inflation.columns
        df_inflation.drop(columns=[columns[0], columns[1]], inplace=True)
        for column in df_inflation:
            try:
                df_inflation[column] = pd.to_numeric(
                df_inflation[column]
                )
            except ValueError:
                continue
        # for column in columns[2:]:
        #     df_inflation[column] = pd.to_numeric(
        #         df_inflation[column]
        #     )
        df_inflation.columns = [int(column) for column in df_inflation]
        df_inflation.fillna(0, inplace=True)
        return df_inflation
    
    def full_package(self):
        self.scraper()
        self.comparative_inflation()


InflationProject().full_package()
# InflationProject().comparative_inflation()