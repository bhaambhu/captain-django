from enum import unique
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from users.models import CaptainUser


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Currently unused in preference of the below.
    """
    email = serializers.EmailField(required=True, validators=[
                                   UniqueValidator(queryset=CaptainUser.objects.all(), message="An account with this E-mail already exists.")])
    display_name = serializers.CharField(required=True)
    password = serializers.CharField(min_length=8, write_only=True)

    class Meta:
        model = CaptainUser
        fields = ('email', 'display_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        print("Create function of serializer called")
        password = validated_data.pop('password', None)
        # as long as the fields are the same, we can just use this
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance
