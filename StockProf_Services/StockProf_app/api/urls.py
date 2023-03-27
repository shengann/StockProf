from django.urls import path, include
from rest_framework.routers import DefaultRouter
from StockProf_app.api.views import getStockData, getFinancialRatosData, getStockProfData, getIndustryTicker, stockList, filterStock, MY_getFinancialRatiosData, MY_getStockPrice

router = DefaultRouter()
urlpatterns = [
    path('stocks/<str:sector>', filterStock.as_view(), name='filterStock'),
    path('stocks', stockList.as_view(), name='stock-List'),
    path('stock/<slug:ticker>',getStockData.as_view(), name='get-Stock-Data'),
    path('stock/financial_ratio',getFinancialRatosData.as_view(), name='getFinancialRatosData'),
    path('stockprof', getStockProfData.as_view(), name='getStockProfData'),
    path('industry/<str:sector>', getIndustryTicker.as_view(),name='getIndustryTicker'),
    path('financial-ratio', MY_getFinancialRatiosData.as_view(),name='MY_getFinancialRatiosData'),
    path('stock-price', MY_getStockPrice.as_view(), name='stock-price')
]
