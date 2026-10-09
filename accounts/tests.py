# Provides Django REST Framework's test case with API request support.
from urllib import response

from rest_framework.test import APITestCase

# Provides standard HTTP status codes such as 200, 400 and 401.
from rest_framework import status

# Retrieves the active user model configured in settings.py.
from django.contrib.auth import get_user_model




# Gets the custom User model configured by AUTH_USER_MODEL.
User = get_user_model()


# Groups all login-related tests into one test class.
class LoginAPITest(APITestCase):

    # Runs before each test method to create fresh test data.
    def setUp(self):

        # Creates a test user with a hashed password.
        # This user is stored in the temporary test database.
        self.user = User.objects.create_user(
            fullname="testuser",
            email="test@test1.com",
            password="TestPassword"
        )

        # Stores the URL of the login API endpoint.
        # Reusing this variable avoids repeating the URL in every test.
        self.url = "/api/accounts/login/"

    # Tests whether valid credentials allow the user to log in.
    def test_login_success(self):

        # Sends a POST request containing the user's email and password.
        # format="json" tells the test client to send JSON data.
        response = self.client.post(
            self.url,
            {
                "email": "test@test1.com",
                "password": "TestPassword"
            },
            format="json"
        )

        # Verifies that the login endpoint returns HTTP 200 OK.
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        # Verifies that the response sets an access-token cookie.
        self.assertIn("access_token", response.cookies)

        # Verifies that the response sets a refresh-token cookie.
        self.assertIn("refresh_token", response.cookies)

    # Tests whether login rejects an incorrect password.
    def test_login_wrong_password(self):

        # Sends a login request with an incorrect email and password.
        response = self.client.post(
            self.url,
            {
                "email": "test@example.com",
                "password": "WrongPassword123!"
            },
            format="json"
        )

        # Verifies that the endpoint rejects the login attempt.
        # Depending on the implementation, it may return HTTP 400 or 401.
        self.assertIn(
            response.status_code,
            [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_401_UNAUTHORIZED
            ]
        )

    # Tests the cookies and response status returned after successful login.
    def test_login_response(self):

        # Sends valid credentials to the login endpoint.
        response = self.client.post(
            self.url,
            {
                "email": "test@test1.com",
                "password": "TestPassword"
            },
            format="json"
        )

        # Confirms that the login request succeeded.
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Checks that the access token is returned as a cookie.
        self.assertIn("access_token", response.cookies)

        # Checks that the refresh token is returned as a cookie.
        self.assertIn("refresh_token", response.cookies)

        # Checks that the CSRF cookie is created.
        # This cookie supports protection against cross-site request forgery.
        self.assertIn("csrftoken", response.cookies)

        # Checks that Django creates a session cookie.
        self.assertIn("sessionid", response.cookies)

        # Confirms that JavaScript cannot directly read the access-token cookie.
        # HttpOnly helps protect the cookie from JavaScript-based theft.
        self.assertTrue(
            response.cookies["access_token"]["httponly"]
        )

        # Confirms that JavaScript cannot directly read the refresh-token cookie.
        self.assertTrue(
            response.cookies["refresh_token"]["httponly"]
        )



class MeAPITest(APITestCase):

    # Creates a test user before each test method.
    def setUp(self):
        self.user = User.objects.create_user(
            fullname="testuser",
            email="test@example.com",
            password="TestPassword123"
        )

        # URL used to log in and obtain the authentication cookie.
        self.login_url = "/api/accounts/login/"

        # URL used to retrieve the currently authenticated user.
        self.me_url = "/api/accounts/me/"

    # Tests whether a logged-in user can access their profile.
    def test_me_authenticated(self):

        # Sends valid credentials to the login endpoint.
        login_response = self.client.post(
            self.login_url,
            {
                "email": "test@example.com",
                "password": "TestPassword123"
            },
            format="json"
        )

        # Verifies that login was successful.
        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK
        )

        # Extracts the access token from the login response cookie.
        access_token = login_response.cookies["access_token"].value

        # Sends the access token with the subsequent profile request.
        self.client.cookies["access_token"] = access_token

        # Requests the authenticated user's profile.
        response = self.client.get(self.me_url)

        # Verifies that the profile request succeeds.
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        # Verifies that the returned profile belongs to the logged-in user.
        self.assertEqual(
            response.data["email"],
            self.user.email
        )

    # Tests whether an unauthenticated user is denied access.
    def test_me_unauthenticated(self):

        # Sends a GET request without logging in or setting a token.
        response = self.client.get(self.me_url)

        # Verifies that access is denied.
        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ]
        )

    # Tests whether a logged-in user can log out successfully.
    def test_logout(self):

        # Logs in using valid credentials.
        login_response = self.client.post(
            self.login_url,
            {
                "email": "test@example.com",
                "password": "TestPassword123"
            },
            format="json"
        )

        # Confirms that login was successful.
        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK
        )

        # Sends a POST request to the logout endpoint.
        response = self.client.post("/api/accounts/logout/")

        # Confirms that logout was successful.
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        # Confirms that the access-token cookie is cleared.
        self.assertEqual(
            response.cookies["access_token"].value,
            ""
        )

        # Confirms that the refresh-token cookie is cleared.
        self.assertEqual(
            response.cookies["refresh_token"].value,
            ""
        )

        # Confirms that the user can no longer access their profile.
        me_response = self.client.get(self.me_url)

        self.assertIn(
            me_response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ]
        )

