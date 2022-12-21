from rest_framework import response
from users.models import CaptainUser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import CustomUserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny


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
