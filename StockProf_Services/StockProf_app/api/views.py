import requests
from rest_framework.response import Response
from rest_framework.views import APIView
from StockProf_app.models import  MY_stock, MY_financialRatios, MY_stockPrice
from StockProf_app.api.serializer import MY_finacial_ratiosSerializer, MY_stockSerializer, MY_stockPriceSerializer
from rest_framework import views
import pandas as pd
from datetime import datetime as dt
from django.utils import timezone
from sklearn.preprocessing import MinMaxScaler
from sklearn.neighbors import LocalOutlierFactor
from sklearn.mixture import BayesianGaussianMixture
from django.http import JsonResponse
from selenium import webdriver
import time
import datetime


class filterStock(APIView):
    def get(self, request, *args, **kwargs):
        sector = self.kwargs['sector']
        stocks = MY_stock.objects.filter(Category=sector)
        serializer = MY_stockSerializer(stocks, many=True)
        return Response(serializer.data)
    
    def delete(self, request, *args, **kwargs):
        sector = self.kwargs['sector']
        stocks = stock.objects.filter(Sector=sector)
        stocks.delete()
        return None

    
class stockList(APIView):
    def get(self, request, format=None):
        stocks = MY_stock.objects.all()
        serializer = MY_stockSerializer(stocks, many=True)
        return Response(serializer.data)
    
class getStockData(views.APIView):
    
    def get(self, request, *args, **kwargs):
        ticker = self.kwargs['ticker']
        stock_object = stock.objects.filter(Symbol=ticker)
        print("stock_object", stock_object)
        fianacial_ratio = financialRatios.objects.filter(ticker__in=stock_object)
        serializer = finacialRatiosSerializer(fianacial_ratio, many=True)
        return Response(serializer.data)
        

class getStockProfData(views.APIView):   
    def post(self, request, format=None):
        ticker_list = request.data.get('ticker_list')
        stockTicker = MY_stock.objects.filter(Symbol__in=ticker_list)
        data = MY_financialRatios.objects.filter(ticker__in=stockTicker)
        print(data)
        data_frame = pd.DataFrame((MY_finacial_ratiosSerializer(data, many=True)).data)
        pd.set_option('display.max_rows', None)
        print("data_frame\n", data_frame)
        data_frame=data_frame.drop(columns=['id'])
        
        scaler = MinMaxScaler()
        columns = ['assetturnover', 'quickratio', 'debttoequity','roe', 'dividendyield', 'pricetoearnings']
        df_norm = pd.DataFrame(scaler.fit_transform(data_frame[columns]))
        df_norm.set_axis(columns, axis=1, inplace=True)
        data_frame= data_frame['ticker']
        data_frame = pd.concat([df_norm, data_frame], axis=1)
        pd.set_option('display.max_rows', None)
        print("data_frame\n", data_frame)
        
        lof = LocalOutlierFactor()
        lof.fit(data_frame[columns])
        lof_scores = -lof.negative_outlier_factor_
        data_frame['lof_score'] = lof_scores
        temp_outlierList = []
        for index, row in data_frame.iterrows():
            if row['lof_score'] > 1.5:
                temp_outlierList.append(row['ticker'])
        outlierList = []
        for ticker_list in temp_outlierList:
            clusteredStocks = MY_stock.objects.filter(Symbol=ticker_list)
            serializer = MY_stockSerializer(clusteredStocks, many=True)
            outlierList.append(serializer.data[0])
        data_frame.drop(data_frame[data_frame["lof_score"] > 1.5].index, inplace=True)
        data_frame = data_frame.reset_index(drop=True)
        pd.set_option('display.max_rows', None)
        print("data_frame_lof\n", data_frame)

        data_frame_clustering = data_frame.drop(columns=['lof_score','ticker'])
        em_clustering = BayesianGaussianMixture(n_components=3)
        em_clustering.fit(data_frame_clustering)
        labels = em_clustering.predict(data_frame_clustering)
        print("labels", labels)
        data_frame['label'] = labels
        data_frame = data_frame.drop(columns=['assetturnover', 'quickratio', 'debttoequity', 'roe', 'dividendyield', 'pricetoearnings', 'lof_score'])
        pd.set_option('display.max_rows', None)
        print("data_frame_clustering\n", data_frame)
        
        groups = data_frame.groupby('label')
        lists = []


        for name, group in groups:
            lists.append(group['ticker'].tolist())

        # Print the list of lists
        print(lists)
        clusteringList=[]
        for ticker_list in lists:
            clusteredStocks = MY_stock.objects.filter(Symbol__in=ticker_list) 
            serializer = MY_stockSerializer(clusteredStocks, many=True)
            clusteringList.append(serializer.data)
        
        print("clusteringList", clusteringList)
        content = {
            'status': 1,
            'portfolio': clusteringList,
            'outlier': outlierList

        }
        return Response(content)
    
class MY_getFinancialRatiosData(views.APIView):
    def get(self, request, *args, **kwargs):
        url = 'https://www.klsescreener.com/v2/screener/quote_results'
        header = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }
        form_data = {'getquote': '1', 'board': '1', 'sector': '42'}
        server = requests.post(url, data=form_data, headers=header)
        output = server.text
        filtered_data = pd.read_html(output)
        filtered_data = pd.DataFrame(filtered_data[0])
        filtered_data = filtered_data[['Name', 'Code', 'Category']]
        filtered_data['Code'] = filtered_data['Code'].apply(lambda x: '{:04d}'.format(int(x)))
        for i, row in filtered_data.iterrows():
            MY_stock.objects.create(Symbol=row['Code'], Category=row['Category'], Name=row['Name'])
        code_list = filtered_data['Code'].tolist()

        for Symbol in code_list:
            print(Symbol)
            url = 'https://www.wsj.com/market-data/quotes/MY/{Symbol}/financials'
            klseScreener_url = 'https://www.klsescreener.com/v2/stocks/view/{Symbol}'
            url = url.format(Symbol=Symbol)
            klseScreener_url = klseScreener_url.format(Symbol=Symbol)

            r = requests.get(url, headers=header)
            r_1 = requests.get(klseScreener_url, headers=header)
            data = pd.read_html(r.text)
            klseScreener_data = pd.read_html(r_1.text)
            dividendyield = pd.DataFrame(klseScreener_data[0])
            dividendyield = dividendyield.rename(columns={0: 'StringColumn', 1: 'NumberColumn'})
            dividendyield = dividendyield.loc[dividendyield['StringColumn'].isin(['DY'])]

            result = pd.concat([pd.DataFrame(data[2]), pd.DataFrame(data[3]), pd.DataFrame(data[4]), pd.DataFrame(data[5]), pd.DataFrame(data[6])])
            result = result.rename(columns={0: 'data'})
            result[['StringColumn', 'NumberColumn']] = result['data'].str.extract('([\s()A-Za-z]+)([-\d.]+)')

            result = result.drop(['data'], axis=1)

            result['StringColumn'] = result['StringColumn'].str.replace(' ', '')
            result = result.loc[result['StringColumn'].isin(['ERatio(TTM)', 'TotalAssetTurnover', 'QuickRatio', 'ReturnonEquity', 'TotalDebttoTotalEquity'])]
            result = result.append(dividendyield, ignore_index=True)

            result = result.set_index('StringColumn').T
            result = result.rename_axis(None, axis=1).reset_index(drop=True)
            result['DY'] = result['DY'].str.replace('%', '')
            result[['ERatio(TTM)', 'TotalAssetTurnover', 'QuickRatio', 'ReturnonEquity', 'TotalDebttoTotalEquity', 'DY']] = result[['ERatio(TTM)', 'TotalAssetTurnover', 'QuickRatio', 'ReturnonEquity', 'TotalDebttoTotalEquity', 'DY']].replace('-', '0')
            result['Code'] = Symbol
            
            for i, row in result.iterrows():
                stockTicker = MY_stock.objects.get(Symbol=Symbol)
                MY_financialRatios.objects.create(ticker=stockTicker, assetturnover=row['TotalAssetTurnover'], quickratio=row['QuickRatio'],
                                                  roe=row['ReturnonEquity'], pricetoearnings=row['ERatio(TTM)'], dividendyield=row['DY'], debttoequity=row['TotalDebttoTotalEquity'])
        return None

class MY_getStockPrice (views.APIView):
    def get(self, request, *args, **kwargs):
        code_list = [
            "0091", "7251", "2739", "7045", "5255", "5199", "5071", "5210", "3042", "7293", "5132", "7277", "5141", "5257", "7228", "7250", "5186", "5133", "7108", "7158", "5142", "5115", "0219", "5243", "4324", "7164", "7253", "5279", "5256", "5218"]


        for Symbol in code_list:
            # Replace with the website URL you want to inspect
            url = 'https://www.bursamalaysia.com/trade/trading_resources/listing_directory/company-profile?stock_code={Symbol}'

            # Configure the browser options
            options = webdriver.ChromeOptions()
            options.add_argument('--disable-extensions')
            # Run the browser in headless mode to avoid opening a window
            options.add_argument('--headless')

            # Create the browser object
            browser = webdriver.Chrome(options=options)
            url = url.format(Symbol=Symbol)
            # Navigate to the website and wait for it to load
            browser.get(url)
            time.sleep(1)  # Wait for 5 seconds to allow the website to load

            # Get all the XHR requests made by the website
            xhr_requests = browser.execute_script(
                "return window.performance.getEntriesByType('resource');")

            # Filter the XHR requests to only include those with the 'xmlhttprequest' type
            xhr_requests = [
                xhr for xhr in xhr_requests if 'xmlhttprequest' in xhr['initiatorType'].lower()]

            print(f"Number of XHR requests: {len(xhr_requests)}")
            request_list = []
            for i, xhr in enumerate(xhr_requests):
                request_list.append(xhr['name'])
            stockprice_url = []
            for url in request_list:
                if "stock_price" in url:
                    print(url)
                    response = requests.get(url)
                    response_json = response.json()
                    historicalPrice_list= response_json['historical_data']['data']
                    for i in historicalPrice_list:
                        date = datetime.datetime.fromtimestamp(i['date'] / 1000.0).date()
                        print(date)
                        if i['vol'] == '-':
                            i['vol'] = 0
                        stockTicker = MY_stock.objects.get(Symbol=Symbol)
                        MY_stockPrice.objects.create(ticker=stockTicker, date=date, open=i['open'], high=i['high'],  low=i['low'],  close=i['close'], volume=i['vol'])
        return None
    
class MY_getComparison (views.APIView):
        def post(self, request, *args, **kwargs):
            portfolio_list = request.data.get('portfolio_list')
            outlier_list = request.data.get('outlier_list')
            initial_date = request.data.get('initial_date')
            final_date = request.data.get('final_date')
            capital_gain_loss_list = []
            for i in portfolio_list:
                initial_list = []
                final_list= []
                for j in i :
                    stockTicker = MY_stock.objects.filter(Symbol=j)
                    first_price = MY_stockPrice.objects.filter(ticker__in=stockTicker, date=initial_date)
                    initial_serializer = MY_stockPriceSerializer(first_price, many=True)
                    initial_list.append(float(initial_serializer.data[0]['open']))
                    final_price = MY_stockPrice.objects.filter(ticker__in=stockTicker, date=final_date)
                    final_serializer = MY_stockPriceSerializer(final_price, many=True)
                    final_list.append(float(final_serializer.data[0]['close']))
                    percent_changes = []

                    for i in range(len(initial_list)):
                        percent_change = (final_list[i] - initial_list[i]) / initial_list[i] * 100.0
                        percent_changes.append(percent_change)
                        

                print(percent_changes)
                average = sum(percent_changes) / len(percent_changes)
                capital_gain_loss_list.append(average)
            
            print('capital_gain_loss_list', capital_gain_loss_list)
            data = {
                'Portfolio': capital_gain_loss_list
            }
            return JsonResponse(data)
