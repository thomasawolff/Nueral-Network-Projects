
from textAnalytics import *

import pyodbc
import seaborn as sn
from sklearn.svm import SVC
from sklearn import svm
import tensorflow as tf
import tensorflow_hub as hub
import tensorflow.compat.v1 as tf
from sklearn.decomposition import PCA
from sklearn.metrics import classification_report,confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


def sentenceVectorizer():
    tf.disable_v2_behavior()
    embedded = []
    file = pd.read_csv('GBvideos2.csv', error_bad_lines=False)
    title = file[['video_id','title']].copy()
    embed = hub.Module(r'C:\Users\moose_f8sa3n2\Google Drive\Research Methods\Course Project\YouTube Data\Unicode Files')
    tf.logging.set_verbosity(tf.logging.ERROR)

    with tf.Session() as session:
        session.run([tf.global_variables_initializer(), tf.tables_initializer()])
        message_embeddings = session.run(embed(title['title']))

    for i, message_embedding in enumerate(np.array(message_embeddings).tolist()):
        message_embedding_snippet = ", ".join((str(x) for x in message_embedding[:3]))
        embedded.append(message_embedding_snippet)
    title['embeddedValue'] = embedded
    title.to_csv('sentencesEncoded2.csv',sep=',',encoding='utf-8')


def databaseConnection():
    dataList = []
    cnxn = pyodbc.connect(r'Driver={SQL Server};Server=DESKTOP-K3QDR1M\MSSQLSERVER20191;Database=YouTube Data Project;Trusted_Connection=yes;')
    cursor = cnxn.cursor()
    cursor.execute("SELECT * from YouTubeDataPivoted")
    cols = [column[0] for column in cursor.description]
    while 1:
        row = cursor.fetchone()
        if not row:
            break
        dataList.append(list(row))
    cnxn.close()
    df = pd.DataFrame(dataList, columns = cols)
    #print(df)

#databaseConnection()


def pandasAggregate():
    data = go.kMeansClustering()
    
    dataPolarity = data[['videoID','sentimentBucket']].copy()
    dataSubjectivity = data[['videoID','subjectivity']].copy()
    dataClusters = data[['videoID','clusters']].copy()

    # this code partitions the data by video ID and counts the number of values in the sentiment bucket column
    # giving each row an incremented value which is then used for the pivot of the data
    dataPolarity['dataRowNumSentiment'] = dataPolarity.sort_values(['videoID','sentimentBucket'], ascending=[True,False])\
             .groupby(['videoID'])\
             .cumcount() + 1

    # this code partitions the data by video ID and counts the number of values in the subjectivity column
    # giving each row an incremented value which is then used for the pivot of the data
    dataSubjectivity['dataRowNumSubjectivity'] = dataSubjectivity.sort_values(['videoID','subjectivity'], ascending=[True,False])\
             .groupby(['videoID'])\
             .cumcount() + 1

    # this code partitions the data by video ID and counts the number of values in the clusters column
    # giving each row an incremented value which is then used for the pivot of the data
    dataClusters['dataRowNumClusters'] = dataClusters.sort_values(['videoID','clusters'], ascending=[True,False])\
             .groupby(['videoID'])\
             .cumcount() + 1

    # this code pivots the data using the fields created above. All values in these fields with be on one row per video ID
    sentimentPivot = dataPolarity.pivot(index='videoID', columns='dataRowNumSentiment', values='sentimentBucket')
    subjectivityPivot = dataSubjectivity.pivot(index='videoID', columns='dataRowNumSubjectivity', values='subjectivity')
    clustersPivot = dataClusters.pivot(index='videoID', columns='dataRowNumClusters', values='clusters')

    sentimentPivot.to_csv('SentimentPartition.csv')
    subjectivityPivot.to_csv('SubjectivityPartition.csv')
    clustersPivot.to_csv('ClustersPartition.csv')

#pandasAggregate()


def dataMerge():
    np.seterr(divide = 'ignore') 
    df = go.dataReturn()
    df = pd.DataFrame(df)
    df = df.set_index('videoID')
    
    encoded = pd.read_csv('sentencesEncoded2.csv')
    clusters = pd.read_csv('ClustersPartitionFinal20.csv')
    subject = pd.read_csv('SubjectivityPartitionFinal20.csv')
    sentiment = pd.read_csv('SentimentPartitionFinal20.csv')

    merge1 = pd.merge(df, encoded, on = 'videoID')
    merge2 = pd.merge(merge1, clusters, on = 'videoID')
    merge3 = pd.merge(merge2, subject, on = 'videoID')
    merge4 = pd.merge(merge3, sentiment, on = 'videoID')

    merge4['views'] = np.log2(merge4['views'])

    merge4.loc[merge4['views'] < 18, 'viewsBucket'] = '1'
    merge4.loc[(merge4['views'] > 18) & (merge4['views'] <= 20), 'viewsBucket'] = '2'
    merge4.loc[(merge4['views'] > 20) & (merge4['views'] <= 22), 'viewsBucket'] = '3'
    merge4.loc[merge4['views'] > 22, 'viewsBucket'] = '4'

    #print(round(merge4['views'].describe(include='all')),2)
    ##    25%        18.0
    ##    50%        20.0
    ##    75%        22.0
    ##    max        29.0
    ##    Name: views, dtype: float64 2
    
    merge4 = merge4.set_index('videoID')
    del merge4['views']
    #merge4.to_csv('dataCombined.csv')
    
    return merge4

    ##    videoID        categoryID views  ...   SentimentKBucket40  viewsBucket                                
    ##    _0d3XbH12cs          10   18.0  ...                   1       2
    ##    _38JDGnr0vA          15   24.0  ...                   1       4
    ##    _4PLKxYZUPc          22   21.0  ...                   1       3
    ##    _5wCA9OM00o          22   19.0  ...                   1       2
    ##    _5ZrSKpbdSg          28   19.0  ...                   1       2
    ##    ...                 ...    ...  ...                 ...          ...
    ##    zyPIdeF4NFI          22   19.0  ...                   1       2
    ##    ZYQ1cVRtMZU          26   24.0  ...                   1       4
    ##    ZYSjPZUqLdk          22   21.0  ...                   1       3
    ##    zZ2CLmvqfXg          24   22.0  ...                   1       3
    ##    Z-zdIGxOJ4M          10   19.0  ...                   1       2
    ##
    ##    [2661 rows x 69 columns]

#dataMerge()


def modelPredictionsSVM():
    data = dataMerge()
    
    X_train, X_test, y_train, y_test = train_test_split(data, data['viewsBucket'], test_size=0.2, random_state=1)
    X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.25, random_state=1)
    
    del X_train['viewsBucket']
    del X_test['viewsBucket']
    del X_val['viewsBucket']

    modelPCA = PCA(n_components = 2).fit(X_train)
    print('Variance Explained by PCA model:',modelPCA.explained_variance_ratio_)
    print('Singlular values of PCA model:',modelPCA.singular_values_)
    modelLR = LogisticRegression()

    X_train_PCA = modelPCA.transform(X_train)
    X_val_PCA = modelPCA.transform(X_val)
    modelLR.fit(X_train_PCA,y_train)
    predictions = modelLR.predict(X_val_PCA)

    print('Train Performance Logistic Regression with PCA: '+str(round(modelLR.score(X_train_PCA,y_train),2)))
    print('Validation Performance Logistic Regression with PCA: '+str(round(+modelLR.score(X_val_PCA,y_val),2)))
    print('Confusion Matrix:')
    print(confusion_matrix(y_val,predictions))
    print('Classification Report:')
    print(classification_report(y_val, predictions))

    print('Cross Validation scores from 8 iterations:')
    scores = cross_val_score(modelLR, X_train_PCA, y_train, cv=8)
    print(scores)

    ##    Variance Explained by PCA model: [0.84009273 0.11403433]
    ##    Singlular values of PCA model: [285.6822093  105.25370206]
    ##    Train Performance Logistic Regression with PCA: 0.42
    ##    Validation Performance Logistic Regression with PCA: 0.39
    ##
    ##    Confusion Matrix:
    ##    [[33 37 29  7]
    ##     [21 30 66 27]
    ##     [15 23 65 51]
    ##     [ 6  6 39 77]]
    ##
    ##    Classification Report:
    ##                  precision    recall  f1-score   support
    ##
    ##               1       0.44      0.31      0.36       106
    ##               2       0.31      0.21      0.25       144
    ##               3       0.33      0.42      0.37       154
    ##               4       0.48      0.60      0.53       128
    ##
    ##        accuracy                           0.39       532
    ##       macro avg       0.39      0.39      0.38       532
    ##    weighted avg       0.38      0.39      0.37       532
    ##
    ##    Cross Validation scores from 8 iterations:
    ##    [0.43  0.47  0.405  0.385  0.462  0.407  0.376  0.432]


modelPredictionsSVM()


    

