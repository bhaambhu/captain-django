from django.db.models.query import Prefetch
from django.db.models.query_utils import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from django.http.response import JsonResponse
from django.db import connection
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from knowledge.models import Subject, Topic, Path, TopicProgress
from .serializers import PathDetailRetrieveSerializer, PathDetailSerializer, PathListSerializer, PathTopicSequenceSerializer, SubjectDetailSerializer, SubjectSerializer, TopicListSerializer, TopicDetailSerializer, TopicProgressMinSerializer, TopicProgressSerializer
from rest_framework.permissions import BasePermission, IsAdminUser, IsAuthenticated, IsAuthenticatedOrReadOnly, SAFE_METHODS
from time import sleep
from django.views.decorators.csrf import csrf_exempt


# Custom Permissions
class IsSuperUser(BasePermission):
    message = "Allowed for superuser only"

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)

@api_view(['GET', 'POST'])
def subjects(request):
    # To get list of subjects (who are children of root)
    if request.method == 'GET':
        try:
            queryset = Subject.objects.get(id=1).get_children()
        except:
            r = Subject(id=1, name='root')
            r.save()
            queryset = Subject.objects.get(id=1).get_children()
        serializer = SubjectSerializer(queryset, many=True)
        return Response(serializer.data)

    # To create a subject with provided name and parentId
    elif request.method == 'POST':
        # Only allow staff to create paths
        if not request.user.is_staff:
            raise PermissionDenied()

        serializer = SubjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def subjectChildren(request, pk):
    if request.method == 'GET':
        try:
            queryset = Subject.objects.get(id=pk).get_children()
        except Subject.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = SubjectSerializer(queryset, many=True)
        return Response(serializer.data)


@api_view(['GET', 'PATCH', 'PUT', 'DELETE'])
def subject(request, pk):

    try:
        thisSubject = Subject.objects.get(id=pk)
    except Subject.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # To get detail of a particular subject
    if request.method == 'GET':
        serializer = SubjectDetailSerializer(thisSubject)
        return Response(serializer.data)

    # To update detail of a particular subject
    elif request.method == 'PUT':
        # Only allow staff to create paths
        if not request.user.is_staff:
            raise PermissionDenied()

        serializer = SubjectDetailSerializer(thisSubject, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # To reparent a subject (update the parent only)
    elif request.method == 'PATCH':
        # Only allow staff to create paths
        if not request.user.is_staff:
            raise PermissionDenied()

        target = Subject.objects.get(id=request.data['targetId'])
        new_pos = request.data['position']
        # Execute move operation
        thisSubject.move_to(target, position=new_pos)
        return Response(status=status.HTTP_200_OK)

    # To delete the subject
    elif request.method == 'DELETE':
        # Only allow staff to create paths
        if not request.user.is_staff:
            raise PermissionDenied()

        thisSubject.delete()
        Subject.objects.rebuild()
        return Response(status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def topics(request):
    # To get list of all topics
    if request.method == 'GET':
        queryset = Topic.objects.all()
        serializer = TopicListSerializer(queryset, many=True)
        return Response(serializer.data)

    # To create a topic with provided data
    elif request.method == 'POST':
        # Only allow staff to create paths
        if not request.user.is_staff:
            raise PermissionDenied()

        serializer = TopicListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def orphanTopics(request):
    # To get list of topics who don't have any subjects
    if request.method == 'GET':
        queryset = Topic.objects.filter(subject=None)
        serializer = TopicListSerializer(queryset, many=True)
        return Response(serializer.data)


@api_view(['GET', 'PATCH', 'PUT', 'DELETE'])
def topic(request, pk):

    try:
        thisTopic = Topic.objects.get(id=pk)
    except Topic.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # To get detail of a particular topic
    if request.method == 'GET':
        serializer = TopicDetailSerializer(thisTopic)
        return Response(serializer.data)

    # To update detail of a particular subject
    elif request.method == 'PUT':
        # Only allow staff to update topics
        if not request.user.is_staff:
            raise PermissionDenied()

        # Clear the requirements because we will fill them again, can this result in lost update if rest requirements make cycle?
        thisTopic.requires.clear()
        # Do a loop to save the "requires" dependencies, if they don't result in cycles
        for oneRequirement in request.data['requires']:
            try:
                requiredTopic = Topic.objects.get(id=oneRequirement['id'])
                # If adding this dependency doesn't create a cycle, add this, otherwise return bad_request
                if WillMakeCycle(pk, oneRequirement['id']):
                    return Response(data="Adding "+oneRequirement['title']+" as a requirement will result in a requirement loop, which is not allowed.", status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Add this reference successfully
                    thisTopic.requires.add(requiredTopic)

            except Topic.DoesNotExist:
                return Response(data="One or more of the added required topics do not exist on the server.", status=status.HTTP_400_BAD_REQUEST)

        # This will save rest of the properties of the topic
        serializer = TopicDetailSerializer(
            thisTopic, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # To reparent a topic (update the subject only)
    elif request.method == 'PATCH':
        # Only allow staff to reparent topics
        if not request.user.is_staff:
            raise PermissionDenied()

        subject = Subject.objects.get(id=request.data['subjectId'])
        thisTopic.subject = subject
        thisTopic.save()
        selectedSubject = Subject.objects.get(
            id=request.data['selectedSubjectId'])
        serializer = SubjectDetailSerializer(selectedSubject)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # To delete the topic
    elif request.method == 'DELETE':
        # Only allow staff to delete topics
        if not request.user.is_staff:
            raise PermissionDenied()

        thisTopic.delete()
        return Response(status=status.HTTP_200_OK)


@api_view(['POST', 'PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def topicRequirement(request, pk, rTopicId):

    try:
        thisTopic = Topic.objects.get(id=pk)
    except Topic.DoesNotExist:
        return Response(data="The current topic does not exist on the server.", status=status.HTTP_404_NOT_FOUND)

    try:
        requiredTopic = Topic.objects.get(id=rTopicId)
    except Topic.DoesNotExist:
        return Response(data="The required topic does not exist on the server.", status=status.HTTP_404_NOT_FOUND)

    # To check if adding this requirement will be safe
    if request.method == 'POST':
        # If adding this dependency will create a cycle send bad_request, otherwise return OK
        if WillMakeCycle(pk, rTopicId):
            return Response(data="Adding '"+requiredTopic.title + "' as a requirement for '" + thisTopic.title + "' will result in a requirement loop, which is not allowed.", status=status.HTTP_400_BAD_REQUEST)
        else:
            # Add this reference successfully
            return Response(data="It's safe to add this dependency.", status=status.HTTP_200_OK)

    # To add the requirement to this topic
    elif request.method == 'PATCH':
        # If adding this dependency doesn't create a cycle, add this, otherwise return bad_request
        if WillMakeCycle(pk, rTopicId):
            return Response(data="Adding '"+requiredTopic.title + "' as a requirement for '" + thisTopic.title + "' will result in a requirement loop, which is not allowed.", status=status.HTTP_400_BAD_REQUEST)
        else:
            # Add this reference successfully
            thisTopic.requires.add(requiredTopic)
            thisTopic.save()
            return Response(TopicProgressMinSerializer(thisTopic.requires.all(), many=True).data, status=status.HTTP_200_OK)

    # To remove this topic from requirements
    elif request.method == 'DELETE':
        thisTopic.requires.remove(rTopicId)
        thisTopic.save()
        return Response(TopicProgressMinSerializer(thisTopic.requires.all(), many=True).data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def paths(request):
    # To get list of paths
    if request.method == 'GET':
        # If requesting user is staff, send all paths
        if (request.user.is_staff):
            queryset = Path.objects.all().order_by('pk')
        else:
            queryset = Path.publishedPaths.all().order_by('pk')

        serializer = PathListSerializer(queryset, many=True)
        return Response(serializer.data)

    # To create a path with provided title, about and published(bool)
    elif request.method == 'POST':
        # Only allow staff to create paths
        if not request.user.is_staff:
            raise PermissionDenied()

        serializer = PathListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def pathDetail(request, pk):

    try:
        thisPath = Path.objects.get(id=pk)
    except Path.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # To get detail of a particular path
    if request.method == 'GET':
        # If non-staff user has requested, only send if its a published path
        if (not thisPath.published and not request.user.is_staff):
            raise PermissionDenied()
            
        queryset = Path.objects.prefetch_related(Prefetch('topic_sequence__topic__progress', queryset=TopicProgress.objects.filter(
            student=request.user.id), to_attr='filtered_progress')).get(id=pk)
        print("Request by "+str(request.user))
        print("Requesting user's id is "+str(request.user.id))
        serializer = PathDetailRetrieveSerializer(queryset)
        return Response(serializer.data)

    # To update detail of a particular path
    elif request.method == 'PUT':
        # Only allow staff to update paths
        if not request.user.is_staff:
            raise PermissionDenied()

        serializer = PathDetailSerializer(thisPath, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # To delete the subject
    elif request.method == 'DELETE':
        # Only allow staff to delete paths
        if not request.user.is_staff:
            raise PermissionDenied()

        thisPath.delete()
        return Response(status=status.HTTP_200_OK)


@api_view(['GET'])
def publishedPaths(request):
    # To get list of paths
    if request.method == 'GET':
        queryset = Path.publishedPaths.all()
        serializer = PathListSerializer(queryset, many=True)
        return Response(serializer.data)

@csrf_exempt
def Progresses(request):
    # List path detail in which topics' progresses are included
    if request.method == 'GET':
        print("Requesting user is "+str(request.user))
        progresses = TopicProgress.objects.filter(student=request.user.id)
        serializer = TopicProgressSerializer(progresses, many=True)
        return JsonResponse(serializer.data, safe=False)


class DataInfo(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request, format=None):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT relname,n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC")
            all = cursor.fetchall()
        return Response(all)

# Helper functions (not views)

def WillMakeCycle(current_topic_id, referenced_topic_id):
    if current_topic_id == referenced_topic_id:
        return True
    else:
        reference = Topic.objects.get(id=referenced_topic_id)
        for furtherReference in reference.requires.all():
            if WillMakeCycle(current_topic_id, furtherReference.id):
                return True
        return False

# Old Code
# class ProgressList(generics.ListCreateAPIView):
#     permission_classes = []
#     queryset = TopicProgress.objects.all()
#     serializer_class = TopicProgressSerializer

#     def list(self, request):
#         print(request.user)
#         # Note the use of `get_queryset()` instead of `self.queryset`
#         queryset = self.get_queryset().filter(student=request.user.id)
#         serializer = TopicProgressSerializer(queryset, many=True)
#         return Response(serializer.data)

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