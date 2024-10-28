from django.core.mail import send_mail
from django.conf import settings
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import CustomUserSerializer,SensorDataSerializer,CustomUser,SensorData, ChangePasswordSerializer, ForgotPasswordSerializer, HealthTipSerializer, RiskAlertSerializer, RiskAlert, HealthTip
from .utils import return_quality_message, generate_random_password
from .aqicalc import calculate_general_aqi



class Authenticate(APIView):

    def get(self, request: Request, *args, **kwargs) -> Response:
        # return super().post(request, *args, **kwargs)
        print(request.data)
        return Response({"data": "ok"},status=status.HTTP_200_OK)

class ReturnSensorData(APIView):
    serializer_class = SensorDataSerializer
    permission_classes = [permissions.AllowAny]

    """ Unified GET method to retrieve data based on query parameters """
    def get(self, request):
        page = request.query_params.get('page')
        latest_data = self.get_latest_sensor_data()
        if page == 'home':
            aqi_percentage, health_condition = calculate_general_aqi(latest_data)
            return Response({
                "general_aqi": aqi_percentage,
                "health_condition": health_condition
            }, status=status.HTTP_200_OK)
        elif page == 'statistics':
            return Response({
                "carbon_monoxide": latest_data.get("carbon_monoxide"),
                "carbon_dioxide": latest_data.get("carbon_dioxide"),
                "lpg_gas": latest_data.get("lpg_gas"),
                "smoke": latest_data.get("smoke"),
                "humidity": latest_data.get("humidity"),
                "temperature": latest_data.get("temperature"),
            }, status=status.HTTP_200_OK)
        return Response({"error": "Invalid page parameter"}, status=status.HTTP_400_BAD_REQUEST)

    def get_latest_sensor_data(self):
        """Retrieve the latest sensor data from the database"""
        try:
            latest_data = SensorData.objects.filter(productID=self.request.user).order_by('-timestamp').first()
            return {
                "carbon_monoxide": latest_data.carbon_monoxide,
                "carbon_dioxide": latest_data.carbon_dioxide,
                "lpg_gas": latest_data.lpg_gas,
                "smoke": latest_data.smoke,
                "humidity": latest_data.humidity,
                "temperature": latest_data.temperature,
            }
        except SensorData.DoesNotExist:
            return {}

class ReceiveSensorData(APIView):
    """ THIS ENPOINT IS USED BY THE ESP32 MODULE TO SEND THE SENSOR DATA TO THE BACKEND """
    serializer_class = SensorDataSerializer
    permission_classes = [permissions.AllowAny]
   
    def post(self, request):
        data = request.data

        serializer = self.serializer_class(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Data saved successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfile(APIView):
    """ THIS ENDPOINT IS USED TO GET/UPDATE USER INFO ON THE SERVER """

    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    # permission_classes = [permissions.AllowAny]

    def get(self,request):
        userSerializer = self.serializer_class(request.user).data
        return Response({"data":userSerializer},status=status.HTTP_200_OK)
    

    def put(self,request):

        user = request.user
        serializer = self.serializer_class(user,data=request.data,partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"data":"ok"},status=status.HTTP_200_OK)

        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class HealthTips(APIView):
    queryset = HealthTip.objects.all()
    serializer_class = HealthTipSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # Get current time and calculate the cutoff time for tips
        # current_time = timezone.now()
        # cutoff_time = current_time - timedelta(minutes=45)
        # return self.queryset.filter(timestamp__gte=cutoff_time)
        return self.queryset
    
    def get(self, request):
        queryset = self.get_queryset()
        latest_tip = queryset.order_by('-timestamp').first()
        previous_tips = queryset.exclude(id=latest_tip.id) if latest_tip else queryset.none()
        response_data = {
            'latest_tip': self.serializer_class(latest_tip).data if latest_tip else None,
            'previous_tips': self.serializer_class(previous_tips, many=True).data
        }
        return Response(response_data)
    
class RiskAlerts(APIView):
    queryset = RiskAlert.objects.all()
    serializer_class = RiskAlertSerializer
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        alerts = []  # List to hold alerts
        lastest_sensor_data = SensorData.objects.filter(productID=request.user).order_by('-timestamp').first()

        # Define the risk elements and thresholds
        risk_elements = RiskAlert.objects.all()

                # Check each risk element against the sensor data
        for risk in risk_elements:
            # Check for CO2 alerts
            if risk.element.lower() == "carbon dioxide":
                alerts.append(return_quality_message(
                    lastest_sensor_data.carbon_dioxide,
                    risk.element,
                    risk.danger_message,
                    risk.solution_message,
                    risk.threshold_bad,
                    risk.threshold_high
                ))

            # Check for CO alerts
            elif risk.element.lower() == "carbon monoxide":
                alerts.append(return_quality_message(
                    lastest_sensor_data.carbon_monoxide,
                    risk.element,
                    risk.danger_message,
                    risk.solution_message,
                    risk.threshold_bad,
                    risk.threshold_high
                ))

            # Check for LPG alerts
            elif risk.element.lower() == "lpg":
                alerts.append(return_quality_message(
                    lastest_sensor_data.lpg_gas,
                    risk.element,
                    risk.danger_message,
                    risk.solution_message,
                    risk.threshold_bad,
                    risk.threshold_high
                ))

            # Check for smoke alerts
            elif risk.element.lower() == "smoke":
                alerts.append(return_quality_message(
                    lastest_sensor_data.smoke,
                    risk.element,
                    risk.danger_message,
                    risk.solution_message,
                    risk.threshold_bad,
                    risk.threshold_high
                ))

            # Check for humidity alerts
            elif risk.element.lower() == "humidity":
                alerts.append(return_quality_message(
                    lastest_sensor_data.humidity,
                    risk.element,
                    risk.danger_message,
                    risk.solution_message,
                    risk.threshold_bad,
                    risk.threshold_high
                ))

            # Check for temperature alerts
            elif risk.element.lower() == "temperature":
                alerts.append(return_quality_message(
                    lastest_sensor_data.temperature,
                    risk.element,
                    risk.danger_message,
                    risk.solution_message,
                    risk.threshold_bad,
                    risk.threshold_high
                ))

        # Return the list of alerts
        return Response([alert for alert in alerts if alert != None])
    
class ChangePassword(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(
            instance=request.user,
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Password changed successfully"}, 
                status=status.HTTP_200_OK
            )
        
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )

class ForgotPassword(APIView):
    queryset = CustomUser.objects.all()
    serializer_class = ForgotPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email_address')

        if not email:
            return Response({"error": "Email address is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(email_address=email)
            new_password = generate_random_password()
            try:
                send_mail(
                    'Password Reset for iBreatheEasy',
                    f'Dear {user.email_address},\n\n'
                    'We have received a request to reset your password for iBreatheEasy.\n\n'
                    f'Your new password is: {new_password}\n\n'
                    'Please use this password to log in to your account. We recommend that you change your password to something more secure as soon as possible.\n\n'
                    'If you have any questions or concerns, please contact us at support@ibreatheasymain.com.\n\n'
                    'Best regards,\n'
                    'The iBreathEasy Team',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email]
                )
                user.set_password(new_password)
                user.save()
                return Response({"message": "New password sent to your email"}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": f"Failed to send email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except CustomUser.DoesNotExist:
            return Response({"error": "Email not found"}, status=status.HTTP_404_NOT_FOUND)

class Logout(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # Get the refresh token from the request body
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Attempt to blacklist the token
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)