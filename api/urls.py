from django.urls import path
from .views import DataInfo, ProgressList, Progresses, subjects, subject, topics, topic, topicRequirement, orphanTopics, subjectChildren, paths, pathDetail, publishedPaths
from rest_framework_swagger.views import get_swagger_view


schema_view = get_swagger_view(title='Captain API')

app_name = 'api'

urlpatterns = [
    path('', schema_view),

    # GET: Get all root level subjects
    # POST: create subject
    path('subjects/', subjects, name='subjectsList'),

    # GET: Get subject in detail
    # PUT: Update subject in detail
    # PATCH: Change subject's parent subject (reparent subject)
    # DELETE: Delete subject
    path('subjects/<int:pk>/', subject, name='subjectDetail'),

    # Get children of particular subject
    path('subjects/<int:pk>/children/',
         subjectChildren, name='subjectChildren'),

    # GET: Get all topics
    # POST: Create topic
    path('topics/', topics, name='topics'),

    # GET: Get topic in detail
    # PUT: Update topic in detail
    # PATCH: Change topic's subject
    # DELETE: Delete topic
    path('topics/<int:pk>/', topic, name='topicDetail'),

    # POST: Check if safe to add requirement
    # PATCH: Add requirement
    # DELETE: Delete requirement
    path('topics/<int:pk>/requires/<int:rTopicId>/', topicRequirement, name='topicRequirement'),

    # GET: Get those topics which don't have any subject assigned to them
    path('topics/orphans/', orphanTopics, name='orphanTopics'),

    path('datainfo/', DataInfo.as_view(), name='dataInfo'),

    path('paths/', paths, name='paths'),
    path('paths/<int:pk>/', pathDetail, name='pathDetail'),
    path('paths/published/', publishedPaths, name='publishedPathsList'),

    # path('progresses/', ProgressList.as_view(), name='progresses'),
    path('progresses/', Progresses, name='progresses'),
]
