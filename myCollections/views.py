import json
import os
from datetime import timedelta
import requests
from collections import Counter
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from rest_framework import status, serializers
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Collections
from .middleware import RequestCounterMiddleware, reset_request_count
from .serializers import CollectionSerializer, UserSerializer


class UserCreateView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            email = request.data.get('email')
            password = request.data.get('password')

            # Validate email and password
            self.get_serializer().validate_email(email)
            self.get_serializer().validate_password(password)

            return super().create(request, *args, **kwargs)

        except serializers.ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserListView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class UserDeleteView(DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        username = instance.username  # Store username before deletion
        self.perform_destroy(instance)
        return Response({"result": f"User '{username}' has been successfully deleted."},
                        status=status.HTTP_204_NO_CONTENT)


# This view has basic user registration logic which gives token as a repsonse
class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    # generates access token for a user and gives it in a response
    def post(self, request):
        username = request.data.get("username", None)
        password = request.data.get("password", None)
        try:
            if username and password:
                user = User.objects.get_or_create(
                    username=username, password=password)
                token = RefreshToken.for_user(user[0], )
                token.access_token.set_exp(lifetime=timedelta(hours=12))
                return Response({'access_token': str(token.access_token)}, status=status.HTTP_200_OK)
            return Response({'error': "Please enter valid username and password"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)


# This view gets the movie list from an intergrated api and
class MoviesListView(APIView):
    permission_classes = [IsAuthenticated]

    # gets movie list from the third party which is then formatted and sent as an response
    def get(self, request):
        username = os.environ.get('MOVIE_API_USERNAME')
        password = os.environ.get('MOVIE_API_PASSWORD')

        if not username or not password:
            return Response({'error': 'Username or password not set in environment variables.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        success = False
        while not success:
            response = requests.get(
                url='https://demo.credy.in/api/v1/maya/movies/',
                headers={"username": username, "password": password},
                verify=False
            )
            if response.status_code == 200:
                success = True
                response = json.loads(response.content.decode("utf-8"))

        return Response(response, status=status.HTTP_200_OK)


# This view creates, edits or deletes collection object of the user
class CollectionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        response = {}
        try:
            collections = Collections.objects.filter(user=request.user)
            if collections.exists():
                movies = list(collections.values("movies"))
                genres_list = [genre for movie in movies[0]["movies"] for genre in movie.get("genres", "").split(",")]
                top_three_genres = [i[0] for i in Counter(genres_list).most_common(3)]
                serializer = CollectionSerializer(instance=collections.first())
                if serializer:
                    response.update({
                        "is_success": True,
                        "data": {
                            "collections": [serializer.data],
                            "favourite_genres": top_three_genres
                        }
                    })
                    return Response(response, status=status.HTTP_200_OK)

            response.update({
                "is_success": True,
                "data": {
                    "collections": "No Data",
                    "favourite_genres": "No Data"
                }
            })
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"is_success": False, 'error': str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # creates movie collection with given title and description
    def post(self, request):
        try:
            if request.user:
                serializer = CollectionSerializer(data=request.data)
                if serializer.is_valid(raise_exception=True):
                    collection = serializer.save()
                    collection.set_user(request.user)
                    return Response({"collection_uuid": collection.uuid}, status=status.HTTP_201_CREATED)

                return Response({"error": "No User"}, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response({"is_success": False, 'error': str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # edits movie collection object having collection_uuid
    def put(self, request, collection_uuid):
        try:
            if request.user:
                collection = Collections.objects.get(uuid=collection_uuid)
                serializer = CollectionSerializer(collection, data=request.data, partial=True)
                if serializer.is_valid(raise_exception=True):
                    collection = serializer.save()
                    collection.set_user(request.user)
                    return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

            return Response({"error": "No Collection or invalid uuid"}, status=status.HTTP_204_NO_CONTENT)

        except ObjectDoesNotExist as ode:
            return Response({"error": f"Collection with collection_uuid {collection_uuid} not found"},
                            status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"is_success": False, 'error': str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # delete movie collection object having collection_uuid
    def delete(self, request, collection_uuid):
        try:
            if request.user:
                collection = Collections.objects.get(uuid=collection_uuid)
                collection.delete()
                return Response({"message": "collection having uuid {collection_uuid} is deleted"},
                                status=status.HTTP_202_ACCEPTED)

            return Response({"error": "No User"}, status=status.HTTP_204_NO_CONTENT)

        except ObjectDoesNotExist as ode:
            return Response({"error": f"Collection with collection_uuid {collection_uuid} not found"},
                            status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response({"is_success": False, 'error': str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)


class CollectionListDetailView(APIView):
    # get movie collection object having collection_uuid
    def get(self, request, collection_uuid):
        try:
            collection = Collections.objects.get(uuid=collection_uuid, user=request.user)
            serializer = CollectionSerializer(collection)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ObjectDoesNotExist as ode:
            return Response({"error": f"Collection with collection_uuid {collection_uuid} not found"},
                            status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"is_success": False, 'error': e}, status.HTTP_500_INTERNAL_SERVER_ERROR)


# This view has get and post request of RequestCounterMiddleware which counts or reset count
class RequestCountView(APIView):
    def get(self, request):
        middleware = RequestCounterMiddleware(get_response=None)
        return Response({f'This is the {middleware.request_count}th request.'}, status=status.HTTP_200_OK)

    def post(self, request):
        response = reset_request_count(request)
        return Response(response.data, status=status.HTTP_200_OK)
