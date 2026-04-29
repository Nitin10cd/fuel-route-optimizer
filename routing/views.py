from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import calculate_fuel_route


class FuelRouteView(APIView):
    """
    POST /api/route/
    
    Request body:
    {
        "start": "New York, NY",
        "end": "Los Angeles, CA"
    }
    """

    def post(self, request):
        start = request.data.get('start', '').strip()
        end   = request.data.get('end', '').strip()

        # Validation
        if not start:
            return Response(
                {'error': 'start location is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not end:
            return Response(
                {'error': 'end location is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if start.lower() == end.lower():
            return Response(
                {'error': 'start and end locations must be different'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate route
        try:
            result = calculate_fuel_route(start, end)
            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {'error': 'Something went wrong. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )