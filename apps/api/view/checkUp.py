from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from ..serializers import MedicalCheckupApplicationSerializer

class MedicalCheckupApplicationView(APIView):
    def post(self, request):
        serializer = MedicalCheckupApplicationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Arizangiz qabul qilindi!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
