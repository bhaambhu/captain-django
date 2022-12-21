from django.urls import path
from .views import AddTopicDependency, Children, DanglingTopicsList, DataInfo, DeleteSubject, DeleteTopicDependency, MoveNode, PathDetail, PathList, ProgressList, Progresses, PublishedPathList, ReparentTopic, SubjectDetail, SubjectList, TopicList, TopicDetail, isDependencySafe
from rest_framework_swagger.views import get_swagger_view


schema_view = get_swagger_view(title='Captain API')

app_name = 'api'

urlpatterns = [
    path('', schema_view),
    path('topics/<int:pk>/', TopicDetail.as_view(), name='topicDetail'),
    path('topics/', TopicList.as_view(), name='topicList'),
    path('danglingtopics/', DanglingTopicsList.as_view(), name='danglingTopics'),
    path('adddependency/', AddTopicDependency, name='addDependency'),
    path('removedependency/', DeleteTopicDependency, name='removeDependency'),
    path('dependencysafe/', isDependencySafe, name='isDependencySafe'),

    path('datainfo/', DataInfo.as_view(), name='dataInfo'),

    path('paths/', PathList.as_view(), name='pathList'),
    path('pubpaths/', PublishedPathList.as_view(), name='pubPathList'),
    path('paths/<int:pk>/', PathDetail.as_view(), name='pathDetail'),

    path('subjects/', SubjectList.as_view(), name='subjectList'),
    path('subjects/<int:pk>/', Children.as_view(), name='subjects'),
    path('subjectdetail/<int:pk>/', SubjectDetail.as_view(), name='subjectDetail'),
    path('movesubject/', MoveNode, name='moveNode'),
    path('deletesubject/', DeleteSubject, name='deleteSubject'),
    path('reparenttopic/', ReparentTopic, name='reparentTopic'),
    # path('progresses/', ProgressList.as_view(), name='progresses'),
    path('progresses/', Progresses, name='progresses'),
]
