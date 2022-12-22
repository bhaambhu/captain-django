from django.db.models.query import Prefetch
from django.db.models.query_utils import Q
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from django.http.response import JsonResponse
from django.db import connection
from rest_framework import generics, status
from rest_framework.response import Response
from knowledge.models import Subject, Topic, Path, TopicProgress
from .serializers import PathDetailRetrieveSerializer, PathDetailSerializer, PathListSerializer, PathTopicSequenceSerializer, SubjectDetailSerializer, SubjectSerializer, TopicListSerializer, TopicDetailSerializer, TopicProgressMinSerializer, TopicProgressSerializer
from rest_framework.permissions import  BasePermission, DjangoModelPermissions, DjangoModelPermissionsOrAnonReadOnly, IsAuthenticated, SAFE_METHODS
from time import sleep
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def Progresses (request):
    """
    List path detail in which topics' progresses are included
    """
    if request.method == 'GET':
        print("Requesting user is "+str(request.user))
        progresses = TopicProgress.objects.filter(student=request.user.id)
        serializer = TopicProgressSerializer(progresses, many=True)
        return JsonResponse(serializer.data, safe=False)

# Check rest_framework docs for other generic classbasedviews, there might be some that are more appropriate

# Generic Views
class ProgressList(generics.ListCreateAPIView):
    permission_classes = []
    queryset = TopicProgress.objects.all()
    serializer_class = TopicProgressSerializer
    def list(self, request):
        print(request.user)
        # Note the use of `get_queryset()` instead of `self.queryset`
        queryset = self.get_queryset().filter(student=request.user.id)
        serializer = TopicProgressSerializer(queryset, many=True)
        return Response(serializer.data)

def WillMakeCycle(current_topic_id, referenced_topic_id):
    if current_topic_id == referenced_topic_id:
        return True
    else:
        reference = Topic.objects.get(id=referenced_topic_id)
        for furtherReference in reference.requires.all():
            if WillMakeCycle(current_topic_id, furtherReference.id):
                return True
        return False


# Why do we have this separate request method instead of adding dependencies via the "save topic" way? Because it allows us to check cycle correctly, for every dependency as we add them one-by-one. The other option was to allow user to add/remove dependencies offline (and only check if adding a dependency will create cycle) and update them on the server via the common "save topic" request. This has a big problem, as checking cycle for an individual dependency through server will give us that there's no cycle, but once multiple "no cycle" dependencies have been added offline by the user and they "save online", there's a chance that they together might lead to a cycle, which will lead to bad user-experience for the subject expert, as the whole "save-topic" request will be rejected.
@api_view(['PATCH'])
def AddTopicDependency(request):
    try:
        currentTopic = Topic.objects.get(id=request.data['ctopic_id'])
        requiredTopic = Topic.objects.get(id=request.data['rtopic_id'])
    except Topic.DoesNotExist:
        return Response(data="Topic does not exist on the server.", status=status.HTTP_400_BAD_REQUEST)
    
    # If adding this dependency doesn't create a cycle, add this, otherwise return bad_request
    if WillMakeCycle(request.data['ctopic_id'], request.data['rtopic_id']):
        return Response(data="Adding this topic makes a requirement loop.", status=status.HTTP_400_BAD_REQUEST)
    else:
        # Add this reference successfully
        currentTopic.requires.add(requiredTopic)
        currentTopic.save()
        return Response(TopicProgressMinSerializer(currentTopic.requires.all(), many=True).data, status=status.HTTP_200_OK)

@api_view(['PATCH'])
def DeleteTopicDependency(request):
    try:
        currentTopic = Topic.objects.get(id=request.data['ctopic_id'])
    except Topic.DoesNotExist:
        return Response(data="Topic does not exist on the server.", status=status.HTTP_400_BAD_REQUEST)
    
    currentTopic.requires.remove(request.data['rtopic_id'])
    currentTopic.save()
    return Response(TopicProgressMinSerializer(currentTopic.requires.all(), many=True).data, status=status.HTTP_200_OK)

@api_view(['PATCH'])
def isDependencySafe(request):
    try:
        requiredTopic = Topic.objects.get(id=request.data['rtopic_id'])
    except Topic.DoesNotExist:
        return Response(data="Topic does not exist on the server.", status=status.HTTP_400_BAD_REQUEST)
    
    # If adding this dependency will create a cycle send bad_request, otherwise return OK
    if WillMakeCycle(request.data['ctopic_id'], request.data['rtopic_id']):
        return Response(data="Adding "+requiredTopic.title+" as a requirement will result in a requirement loop, which is not allowed.", status=status.HTTP_400_BAD_REQUEST)
    else:
        # Add this reference successfully
        return Response(data="It's safe to add this dependency.", status=status.HTTP_200_OK)

@api_view(['PATCH'])
def DeleteSubject(request):
    subject = Subject.objects.get(id=request.data['id'])
    subject.delete()
    Subject.objects.rebuild()
    return Response(status=200)

@api_view(['PATCH'])
def ReparentTopic(request):
    topic = Topic.objects.get(id=request.data['topic_id'])
    subject = Subject.objects.get(id=request.data['subject_id'])
    topic.subject = subject
    topic.save()
    source_subject = Subject.objects.get(id=request.data['source_subject_id'])
    # Execute move operation
    return Response(SubjectDetailSerializer(source_subject).data, status=status.HTTP_200_OK)

@api_view(['PATCH'])
def MoveNode(request):
    source = Subject.objects.get(id=request.data['sourceid'])
    target = Subject.objects.get(id=request.data['targetid'])
    new_pos = request.data['position']
    # Execute move operation
    source.move_to(target, position=new_pos)
    return Response(status=200)

@api_view(['PATCH'])
def DeleteSubject(request):
    subject = Subject.objects.get(id=request.data['id'])
    subject.delete()
    Subject.objects.rebuild()
    return Response(status=200)

class Children(generics.ListCreateAPIView):
    permission_classes = []
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    def list(self, request, *args, **kwargs):
        queryset = Subject.objects.get(id=kwargs['pk']).get_children()
        print("Request by "+str(self.request.user))
        serializer = SubjectSerializer(queryset, many=True)
        return Response(serializer.data)

class SubjectList(generics.ListCreateAPIView):
    permission_classes = []
    # querysetSingle = Subject.objects.filter(id=1)
    # try:
    #     queryset = Subject.objects.get(id=1).get_children()
    # except:
    #     r = Subject(id=1, name='root')
    #     r.save()
    #     queryset = Subject.objects.get(id=1).get_children()
    queryset = Subject.objects.get(id=1).get_children()
    
    # queryset = querysetSingle | querysetSingle[0].get_children()
    # queryset = Subject.objects.filter(Q(level=0) | Q(parent__level = 0))
    serializer_class = SubjectSerializer
    def create(self, request, *args, **kwargs):
        parentObject = Subject.objects.get(id=request.data['parentId'])
        newObject = Subject.objects.create(name=request.data['name'], parent=parentObject)
        return Response(SubjectSerializer(newObject).data, status=status.HTTP_201_CREATED)

class PathList(generics.ListCreateAPIView):
    permission_classes = []
    queryset = Path.objects.all().order_by('pk')
    serializer_class = PathListSerializer

class PublishedPathList(generics.ListAPIView):
    permission_classes = []
    queryset = Path.publishedPaths.all()
    serializer_class = PathListSerializer
    
class SubjectDetail(generics.RetrieveUpdateAPIView):
    permission_classes = []
    queryset = Subject.objects.all()
    serializer_class = SubjectDetailSerializer
    # def retrieve(self, request, *args, **kwargs):
    #     # queryset = Path.objects.get(id=kwargs['pk'])
    #     queryset = Path.objects.prefetch_related(Prefetch('topic_sequence__topic__progress', queryset=TopicProgress.objects.filter(student=self.request.user.id), to_attr='filtered_progress')).get(id=kwargs['pk'])
    #     print("Request by "+str(self.request.user))
    #     serializer = PathDetailRetrieveSerializer(queryset)
    #     return Response(serializer.data)

class PathDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = []
    queryset = Path.objects.all()
    serializer_class = PathDetailSerializer
    def retrieve(self, request, *args, **kwargs):
        # queryset = Path.objects.get(id=kwargs['pk'])
        queryset = Path.objects.prefetch_related(Prefetch('topic_sequence__topic__progress', queryset=TopicProgress.objects.filter(student=self.request.user.id), to_attr='filtered_progress')).get(id=kwargs['pk'])
        print("Request by "+str(self.request.user))
        serializer = PathDetailRetrieveSerializer(queryset)
        return Response(serializer.data)
    
class TopicList(generics.ListCreateAPIView):
    permission_classes = []
    queryset = Topic.objects.all()
    serializer_class = TopicListSerializer
    def create(self, request, *args, **kwargs):
        parentObject = Subject.objects.get(id=request.data['parentId'])
        newObject = Topic.objects.create(title=request.data['name'], subject=parentObject)
        return Response(TopicListSerializer(newObject).data, status=status.HTTP_201_CREATED)

# Dangerous as it can be accessed by anyone
class DataInfo(APIView):
    permission_classes = []
    def get(self, request, format=None):
        with connection.cursor() as cursor:
            cursor.execute("SELECT relname,n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC")
            all = cursor.fetchall()
        return Response(all)

class DanglingTopicsList(generics.ListCreateAPIView):
    permission_classes = []
    queryset = Topic.objects.filter(subject=None)
    serializer_class = TopicListSerializer

class TopicDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = []
    queryset = Topic.objects.all()
    serializer_class = TopicDetailSerializer
    def update(self, request, *args, **kwargs):
        # Get the current topic object
        currentTopic = Topic.objects.get(id=request.data['id'])
        currentTopic.requires.clear()
        # Do a loop to save the "requires" dependencies, if they don't result in cycles
        for oneRequirement in request.data['requires']:
            try:
                requiredTopic = Topic.objects.get(id=oneRequirement['id'])
                # If adding this dependency doesn't create a cycle, add this, otherwise return bad_request
                if WillMakeCycle(request.data['id'], oneRequirement['id']):
                    return Response(data="Adding "+oneRequirement['title']+" as a requirement will result in a requirement loop, which is not allowed.", status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Add this reference successfully
                    currentTopic.requires.add(requiredTopic)

            except Topic.DoesNotExist:
                return Response(data="Topic does not exist on the server.", status=status.HTTP_400_BAD_REQUEST)
            
        # This will save rest of the properties of the topic
        return super().update(request, *args, **kwargs)
    # def update(self, request, *args, **kwargs):
    #     print(request.data)
    #     return Response(data='Theek h', status=status.HTTP_200_OK)

# class TopicList(generics.ListCreateAPIView):
#     permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
#     queryset = Topic.topicobjects.all()
#     serializer_class = TopicSerializer

# Custom Permissions
# class TopicUserWritePermission(BasePermission):
#     message = 'Editing topics is restricted to the author only.'
#     def has_object_permission(self, request, view, obj):
#         if (request.method in SAFE_METHODS) or request.user.is_superuser:
#             return True
#         return obj.author == request.user

# class TopicDetail(generics.RetrieveUpdateAPIView, TopicUserWritePermission):
#     permission_classes = [DjangoModelPermissions, TopicUserWritePermission]
#     queryset = Topic.objects.all()
#     serializer_class = TopicDetailSerializer