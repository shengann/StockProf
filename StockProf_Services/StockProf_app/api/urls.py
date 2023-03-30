from django.urls import path, include
from rest_framework.routers import DefaultRouter
from StockProf_app.api.views import getStockData, getStockProfData, stockList, filterStock, MY_getFinancialRatiosData, MY_getStockPrice, MY_getComparison

router = DefaultRouter()
urlpatterns = [
    path('stocks/<str:Category>', filterStock.as_view(), name='filterStock'),
    path('stocks', stockList.as_view(), name='stock-List'),
    path('stock/<slug:ticker>',getStockData.as_view(), name='get-Stock-Data'),
    path('stockprof', getStockProfData.as_view(), name='getStockProfData'),
    path('financial-ratio', MY_getFinancialRatiosData.as_view(),name='MY_getFinancialRatiosData'),
    path('stock-price', MY_getStockPrice.as_view(), name='stock-price'),
    path('comparison', MY_getComparison.as_view(), name='comparison')
]
