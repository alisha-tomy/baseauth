from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.views import APIView

from django.contrib.auth import get_user_model
from django.db.models import Q


class AutoComplete(APIView):
    """An endpoint for autocomplete functionality."""

    serializer_class = None
    schema = AutoSchema()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='q',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Search query',
            ),
            OpenApiParameter(
                name='limit',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Limit the number of results',
            ),
            OpenApiParameter(
                name='type',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Search type',
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        """Get autocomplete results based on search query.

        Parameters:
        - q: Search query string.
        - limit: Limit the number of results (default: 100).
        - type: Type of search (comma-separated).

        Returns:
        - Response containing autocomplete results.
        """
        # Retrieve query parameters from the request
        searchstr = request.GET.get('q')
        searchtype = request.GET.get('type')
        limit = request.GET.get('limit')

        # Validate and set the limit parameter
        try:
            limit = int(limit) if limit else 100
        except ValueError:
            return Response(
                'Limit should be an integer', status=status.HTTP_400_BAD_REQUEST
            )

        # Parse the search type parameter
        typelist = (
            [t.lower().strip() for t in searchtype.split(',')] if searchtype else None
        )

        # Check if search query is provided
        if not searchstr:
            return Response(
                'The search query string is not provided.',
                status=status.HTTP_400_BAD_REQUEST,
            )
        if (typelist and 'user' in typelist) or not typelist:
            UserModel = get_user_model()
            # Construct the query
            query = (
                Q(first_name__icontains=searchstr)
                | Q(last_name__icontains=searchstr)
                | Q(username__icontains=searchstr)
            )
            users = UserModel.objects.filter(query)

            # Apply the limit if provided
            users = users[:limit] if limit else users

            # Format the response data
            data = [
                {
                    'id': user.username,
                    'label': f'{user.first_name} {user.last_name}'
                    if user.first_name and user.last_name
                    else user.first_name
                    if user.first_name
                    else user.last_name
                    if user.last_name
                    else user.username,
                }
                for user in users
            ]

            # Return response
            return Response(
                [{'id': 'Django Auth User', 'label': 'User', 'data': data}]
                if (typelist and 'user' in typelist)
                else data
            )
        else:
            # Invalid type parameter
            return Response(
                'Type parameter should either be empty or include user',
                status=status.HTTP_400_BAD_REQUEST,
            )
