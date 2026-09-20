import pandas as pd
import matplotlib.pyplot as plt
import src.layout

from src.layout import create_layout


 
print("LAYOUT MODULE BEING USED:")
print(src.layout.__file__)
  


print("create_layout is coming from:")
print(create_layout.__module__)

 
print("FUNCTION SOURCE:")
  

import inspect

source = inspect.getsource(create_layout)

print(source)


  
# TEST DATA
  

bathroom_width = 6
bathroom_depth = 8

products = pd.DataFrame([
    {
        "name": "Example Toilet",
        "category": "Toilet",
        "width_cm": 40,
        "depth_cm": 70
    },
    {
        "name": "Example Vanity",
        "category": "Vanity",
        "width_cm": 80,
        "depth_cm": 45
    },
    {
        "name": "Example Faucet",
        "category": "Faucet",
        "width_cm": 20,
        "depth_cm": 20
    },
    {
        "name": "Example Shower",
        "category": "Shower",
        "width_cm": 90,
        "depth_cm": 90
    }
])


 
print("PRODUCTS:")
  

print(
    products[
        ["category", "width_cm", "depth_cm"]
    ]
)


  
# CREATE LAYOUT
  

fig = create_layout(
    bathroom_width,
    bathroom_depth,
    products
)

plt.show()