from rest_framework import response
from users.models import CaptainUser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import CustomUserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import api_view, permission_classes
from users.models import CaptainUser
from .serializers import CaptainUserSUSerializer, CaptainUserInfoSerializer
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS


# Custom Permissions

class IsSuperUser(BasePermission):
    message = "Allowed for superuser only"

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class UserInfoWritePermission(BasePermission):
    message = 'Editing user info is restricted to the user only.'

    def has_object_permission(self, request, view, obj):
        if (request.method in SAFE_METHODS) or request.user.is_superuser:
            return True
        return obj.id == request.user.id

# Views


@api_view(['GET'])
@permission_classes([IsSuperUser])
def allUsers(request):
    # To get list of subjects (who are children of root)
    if request.method == 'GET':
        queryset = CaptainUser.objects.all()
        serializer = CaptainUserSUSerializer(queryset, many=True)
        return Response(serializer.data)


@api_view(['GET', 'PUT', 'DELETE', 'PATCH'])
@permission_classes([IsAuthenticated])
def userInfo(request, pk):
    try:
        userObject = CaptainUser.objects.get(id=pk)
        if (not request.user.is_superuser and userObject.id != request.user.id):
            raise PermissionDenied()

    except CaptainUser.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # To get info of a particular user
    if request.method == 'GET':
        serializer = CaptainUserInfoSerializer(userObject)
        return Response(serializer.data)

    # To update info of a particular user
    if request.method == 'PUT':
        serializer = CaptainUserInfoSerializer(userObject, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # To change staff status of a particular user (only superuser can do this)
    if request.method == 'PATCH':
        if not request.user.is_superuser:
            raise PermissionDenied()

        # Prevent changing the is_staff property of superusers
        if userObject.is_superuser:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

        new_staff_status = request.data['isStaff']
        try:
            userObject.is_staff = new_staff_status
            userObject.save()
            serializer = CaptainUserSUSerializer(userObject)
            return Response(serializer.data)
        except:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # To delete a particular user
    elif request.method == 'DELETE':
        userObject.delete()
        return Response(status=status.HTTP_200_OK)

class CustomUserCreate(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format='json'):
        print("custom user create called:")
        user = request.data
        serializer = CustomUserSerializer(data=user)
        # # New part - testing
        # serializer.is_valid(raise_exception=True)
        # try:
        #     user = CaptainUser.objects.create_user(
        #         email=serializer.data.get("email"),
        #         password=request.data.get("password"),
        #     )
        # except IntegrityError:
        #     return Response("E-mail already exists.", status=status.HTTP_406_NOT_ACCEPTABLE,
        #     )

        # This part commented - testing
        if serializer.is_valid():
            user = serializer.save()
            if user:
                json = serializer.data
                print("serializer data:")
                print(json)
                return Response(json, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BlacklistTokenUpdateView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
