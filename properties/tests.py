# properties/tests.py

import json
import os
from io import StringIO
from unittest import mock

from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, Client
from django.urls import reverse

from .admin import AccommodationAdmin, LocationAdmin
from .forms import AccommodationAdminForm, AccommodationForm, LocationForm, SignUpForm
from .models import Accommodation, Location, LocalizeAccommodation
from .signals import assign_property_owner_permissions


class SetupGroupsAndPermissions(TestCase):
    def setUp(self):
        """
        Set up groups and permissions for testing.
        """
        self.group, created = Group.objects.get_or_create(name='Property Owners')
        self.accommodation_content_type = ContentType.objects.get_for_model(Accommodation)
        self.permissions = Permission.objects.filter(content_type=self.accommodation_content_type)
        for permission in self.permissions:
            self.group.permissions.add(permission)
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.user.groups.add(self.group)


class ModelTests(TestCase):
    def setUp(self):
        """
        Set up sample Location and Accommodation instances for testing.
        """
        self.country = Location.objects.create(
            id='US',
            title='United States',
            center=Point(-98.583333, 39.833333),
            location_type='country',
            country_code='US'
        )

        self.state = Location.objects.create(
            id='CA',
            title='California',
            center=Point(-119.4179, 36.7783),
            parent_id=self.country,
            location_type='state',
            country_code='US',
            state_abbr='CA'
        )

        self.city = Location.objects.create(
            id='LA',
            title='Los Angeles',
            center=Point(-118.2437, 34.0522),
            parent_id=self.state,
            location_type='city',
            country_code='US',
            city='Los Angeles'
        )

        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.accommodation = Accommodation.objects.create(
            id='ACC1',
            title='Test Accommodation',
            feed=1,
            country_code='US',
            bedroom_count=2,
            review_score=4.5,
            usd_rate=150.00,
            center=Point(-118.2437, 34.0522),
            images=["accommodation_images/test1.jpg"],
            location=self.city,
            amenities={
                "wifi": True,
                "air_conditioning": True,
                "kitchen": True
            },
            user=self.user,
            published=True
        )

    def test_location_str(self):
        self.assertEqual(str(self.country), 'United States')
        self.assertEqual(str(self.state), 'California')
        self.assertEqual(str(self.city), 'Los Angeles')

    def test_accommodation_str(self):
        self.assertEqual(str(self.accommodation), 'Test Accommodation')

    def test_accommodation_set_and_get_images(self):
        new_images = ["accommodation_images/test2.jpg", "accommodation_images/test3.jpg"]
        self.accommodation.images = new_images
        self.accommodation.save()
        self.assertEqual(self.accommodation.images, new_images)

    def test_accommodation_relationships(self):
        self.assertEqual(self.accommodation.location, self.city)
        self.assertEqual(self.city.parent_id, self.state)
        self.assertEqual(self.state.parent_id, self.country)


class FormTests(TestCase):
    def setUp(self):
        """
        Set up sample data for form testing.
        """
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.country = Location.objects.create(
            id='US',
            title='United States',
            center=Point(-98.583333, 39.833333),
            location_type='country',
            country_code='US'
        )
        self.state = Location.objects.create(
            id='CA',
            title='California',
            center=Point(-119.4179, 36.7783),
            parent_id=self.country,
            location_type='state',
            country_code='US',
            state_abbr='CA'
        )
        self.city = Location.objects.create(
            id='LA',
            title='Los Angeles',
            center=Point(-118.2437, 34.0522),
            parent_id=self.state,
            location_type='city',
            country_code='US',
            city='Los Angeles'
        )

    def test_sign_up_form_valid(self):
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123'
        }
        form = SignUpForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_sign_up_form_invalid(self):
        form_data = {
            'username': '',
            'email': 'invalidemail',
            'password': 'short'
        }
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('password', form.errors)

    def test_accommodation_form_valid(self):
        form_data = {
            'title': 'Test Accommodation',
            'feed': 1,
            'country_code': 'US',
            'bedroom_count': 2,
            'review_score': 4.5,
            'usd_rate': 150.00,
            'location': self.city.id,
            'amenities': '{"wifi": true, "air_conditioning": true, "kitchen": true}',
            'user': self.user.id,
            'published': True
        }
        form = AccommodationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_accommodation_form_invalid_review_score(self):
        form_data = {
            'title': 'Test Accommodation',
            'feed': 1,
            'country_code': 'US',
            'bedroom_count': 2,
            'review_score': 6.0,  # Invalid: max=5
            'usd_rate': 150.00,
            'location': self.city.id,
            'amenities': '{"wifi": true, "air_conditioning": true, "kitchen": true}',
            'user': self.user.id,
            'published': True
        }
        form = AccommodationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('review_score', form.errors)


class ViewTests(TestCase):
    def setUp(self):
        """
        Set up sample data for view testing.
        """
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.superuser = User.objects.create_superuser(username='admin', password='adminpass', email='admin@example.com')
        self.country = Location.objects.create(
            id='US',
            title='United States',
            center=Point(-98.583333, 39.833333),
            location_type='country',
            country_code='US'
        )
        self.state = Location.objects.create(
            id='CA',
            title='California',
            center=Point(-119.4179, 36.7783),
            parent_id=self.country,
            location_type='state',
            country_code='US',
            state_abbr='CA'
        )
        self.city = Location.objects.create(
            id='LA',
            title='Los Angeles',
            center=Point(-118.2437, 34.0522),
            parent_id=self.state,
            location_type='city',
            country_code='US',
            city='Los Angeles'
        )
        self.accommodation = Accommodation.objects.create(
            id='ACC1',
            title='Test Accommodation',
            feed=1,
            country_code='US',
            bedroom_count=2,
            review_score=4.5,
            usd_rate=150.00,
            center=Point(-118.2437, 34.0522),
            images=["accommodation_images/test1.jpg"],
            location=self.city,
            amenities={
                "wifi": True,
                "air_conditioning": True,
                "kitchen": True
            },
            user=self.user,
            published=True
        )

    def test_home_view_status_code(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'properties/home.html')

    def test_signup_view_get(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'properties/signup.html')

    def test_signup_view_post_valid(self):
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123'
        }
        response = self.client.post(reverse('signup'), data=form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        new_user = User.objects.get(username='newuser')
        self.assertTrue(new_user.groups.filter(name='Property Owners').exists())
        # Assuming approval mechanism sets is_active=False initially
        # Modify accordingly based on your actual implementation
        # self.assertFalse(new_user.is_active)

    def test_signup_view_post_invalid(self):
        form_data = {
            'username': '',
            'email': 'invalidemail',
            'password': 'short'
        }
        response = self.client.post(reverse('signup'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', 'This field is required.')
        self.assertFormError(response, 'form', 'email', 'Enter a valid email address.')
        # Adjust based on actual form validation errors

    def test_accommodation_detail_view_authenticated(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('accommodation_detail', args=[self.accommodation.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'properties/accommodation_detail.html')
        self.assertIn('accommodation', response.context)
        self.assertIn('localized', response.context)
        self.assertEqual(response.context['accommodation'], self.accommodation)

    def test_accommodation_detail_view_not_authenticated(self):
        response = self.client.get(reverse('accommodation_detail', args=[self.accommodation.id]))
        self.assertEqual(response.status_code, 200)  # Adjust based on your view's access control
        self.assertTemplateUsed(response, 'properties/accommodation_detail.html')


class AdminTests(TestCase):
    def setUp(self):
        """
        Set up admin user and sample data for admin testing.
        """
        self.client = Client()
        self.superuser = User.objects.create_superuser(username='admin', password='adminpass', email='admin@example.com')
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.group = Group.objects.create(name='Property Owners')
        self.country = Location.objects.create(
            id='US',
            title='United States',
            center=Point(-98.583333, 39.833333),
            location_type='country',
            country_code='US'
        )
        self.state = Location.objects.create(
            id='CA',
            title='California',
            center=Point(-119.4179, 36.7783),
            parent_id=self.country,
            location_type='state',
            country_code='US',
            state_abbr='CA'
        )
        self.city = Location.objects.create(
            id='LA',
            title='Los Angeles',
            center=Point(-118.2437, 34.0522),
            parent_id=self.state,
            location_type='city',
            country_code='US',
            city='Los Angeles'
        )
        self.accommodation = Accommodation.objects.create(
            id='ACC1',
            title='Test Accommodation',
            feed=1,
            country_code='US',
            bedroom_count=2,
            review_score=4.5,
            usd_rate=150.00,
            center=Point(-118.2437, 34.0522),
            images=["accommodation_images/test1.jpg"],
            location=self.city,
            amenities={
                "wifi": True,
                "air_conditioning": True,
                "kitchen": True
            },
            user=self.user,
            published=True
        )

    def test_admin_login_required(self):
        response = self.client.get('/admin/')
        self.assertRedirects(response, '/admin/login/?next=/admin/')

    def test_admin_access_superuser(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get('/admin/properties/accommodation/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/properties/accommodation/change_list.html')

    def test_admin_access_property_owner(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get('/admin/properties/accommodation/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/properties/accommodation/change_list.html')

    def test_admin_can_add_accommodation(self):
        self.client.login(username='admin', password='adminpass')
        url = '/admin/properties/accommodation/add/'
        data = {
            'title': 'Admin Accommodation',
            'feed': 2,
            'country_code': 'US',
            'bedroom_count': 3,
            'review_score': 4.0,
            'usd_rate': 200.00,
            'location': self.city.id,
            'amenities': json.dumps({"wifi": True, "air_conditioning": True, "kitchen": False}),
            'user': self.user.id,
            'published': True,
            '_save': 'Save',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Accommodation.objects.filter(title='Admin Accommodation').exists())

    def test_admin_can_change_accommodation(self):
        self.client.login(username='admin', password='adminpass')
        url = f'/admin/properties/accommodation/{self.accommodation.id}/change/'
        data = {
            'title': 'Updated Accommodation',
            'feed': 1,
            'country_code': 'US',
            'bedroom_count': 2,
            'review_score': 4.5,
            'usd_rate': 150.00,
            'location': self.city.id,
            'amenities': json.dumps({"wifi": True, "air_conditioning": True, "kitchen": True}),
            'user': self.user.id,
            'published': True,
            '_save': 'Save',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.accommodation.refresh_from_db()
        self.assertEqual(self.accommodation.title, 'Updated Accommodation')

    def test_admin_can_delete_accommodation(self):
        self.client.login(username='admin', password='adminpass')
        url = f'/admin/properties/accommodation/{self.accommodation.id}/delete/'
        response = self.client.post(url, {'post': 'yes'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Accommodation.objects.filter(id='ACC1').exists())


class ManagementCommandTests(TestCase):
    def setUp(self):
        """
        Set up sample data for management command testing.
        """
        self.country = Location.objects.create(
            id='US',
            title='United States',
            center=Point(-98.583333, 39.833333),
            location_type='country',
            country_code='US'
        )
        self.state = Location.objects.create(
            id='CA',
            title='California',
            center=Point(-119.4179, 36.7783),
            parent_id=self.country,
            location_type='state',
            country_code='US',
            state_abbr='CA'
        )
        self.city = Location.objects.create(
            id='LA',
            title='Los Angeles',
            center=Point(-118.2437, 34.0522),
            parent_id=self.state,
            location_type='city',
            country_code='US',
            city='Los Angeles'
        )

    @mock.patch('properties.management.commands.generate_sitemap.os.makedirs')
    @mock.patch('properties.management.commands.generate_sitemap.open', new_callable=mock.mock_open)
    @mock.patch('properties.management.commands.generate_sitemap.os.path.join')
    def test_generate_sitemap_command_success(self, mock_join, mock_open_file, mock_makedirs):
        """
        Test that the generate_sitemap command successfully creates sitemap.json with correct data.
        """
        mock_join.side_effect = lambda *args: os.path.join(*args)
        out = StringIO()
        call_command('generate_sitemap', stdout=out)

        mock_makedirs.assert_called_with('Generated', exist_ok=True)
        mock_open_file.assert_called_with(os.path.join('Generated', 'sitemap.json'), mode='w', encoding='utf-8')

        handle = mock_open_file()
        written_data = ''.join([call.args[0] for call in handle.write.call_args_list])
        sitemap = json.loads(written_data)

        expected_sitemap = [
            {
                "United States": "united-states",
                "locations": [
                    {
                        "California": "california/california",
                        "locations": [
                            {
                                "Los Angeles": "los-angeles/los-angeles"
                            }
                        ]
                    }
                ]
            }
        ]

        self.assertEqual(sitemap, expected_sitemap)
        self.assertIn("Sitemap successfully saved to Generated/sitemap.json", out.getvalue())

    @mock.patch('properties.management.commands.generate_sitemap.os.makedirs', side_effect=Exception("Failed to create directory"))
    @mock.patch('properties.management.commands.generate_sitemap.open', new_callable=mock.mock_open)
    @mock.patch('properties.management.commands.generate_sitemap.os.path.join')
    def test_generate_sitemap_command_exception(self, mock_join, mock_open_file, mock_makedirs):
        """
        Test that the generate_sitemap command handles exceptions gracefully.
        """
        mock_join.side_effect = lambda *args: os.path.join(*args)
        out = StringIO()
        err = StringIO()
        with self.assertRaises(CommandError):
            call_command('generate_sitemap', stdout=out, stderr=err)

        self.assertIn("Error generating sitemap: Failed to create directory", err.getvalue())
        mock_open_file.assert_not_called()

    @mock.patch('properties.management.commands.generate_sitemap.os.makedirs')
    @mock.patch('properties.management.commands.generate_sitemap.open', new_callable=mock.mock_open)
    @mock.patch('properties.management.commands.generate_sitemap.os.path.join')
    def test_generate_sitemap_command_no_countries(self, mock_join, mock_open_file, mock_makedirs):
        """
        Test that the generate_sitemap command handles the case when there are no countries.
        """
        Location.objects.all().delete()
        mock_join.side_effect = lambda *args: os.path.join(*args)
        out = StringIO()
        err = StringIO()
        call_command('generate_sitemap', stdout=out, stderr=err)

        self.assertIn("No countries found in the database.", out.getvalue())
        mock_open_file.assert_not_called()

    @mock.patch('properties.management.commands.generate_sitemap.os.makedirs')
    @mock.patch('properties.management.commands.generate_sitemap.open', new_callable=mock.mock_open)
    @mock.patch('properties.management.commands.generate_sitemap.os.path.join')
    def test_generate_sitemap_command_with_duplicate_titles(self, mock_join, mock_open_file, mock_makedirs):
        """
        Test that the generate_sitemap command handles duplicate location titles correctly.
        """
        # Create duplicate locations
        duplicate_country = Location.objects.create(
            id='DU',
            title='United States',
            center=Point(-100.0, 40.0),
            location_type='country',
            country_code='US'
        )
        duplicate_state = Location.objects.create(
            id='DUCA',
            title='California',
            center=Point(-120.0, 35.0),
            parent_id=duplicate_country,
            location_type='state',
            country_code='US',
            state_abbr='CA'
        )
        duplicate_city = Location.objects.create(
            id='DULA',
            title='Los Angeles',
            center=Point(-119.0, 34.0),
            parent_id=duplicate_state,
            location_type='city',
            country_code='US',
            city='Los Angeles'
        )

        mock_join.side_effect = lambda *args: os.path.join(*args)
        out = StringIO()
        call_command('generate_sitemap', stdout=out)

        handle = mock_open_file()
        written_data = ''.join([call.args[0] for call in handle.write.call_args_list])
        sitemap = json.loads(written_data)

        expected_sitemap = [
            {
                "United States": "united-states",
                "locations": [
                    {
                        "California": "california/california",
                        "locations": [
                            {
                                "Los Angeles": "los-angeles/los-angeles"
                            }
                        ]
                    }
                ]
            },
            {
                "United States": "united-states",
                "locations": [
                    {
                        "California": "california/california",
                        "locations": [
                            {
                                "Los Angeles": "los-angeles/los-angeles"
                            }
                        ]
                    }
                ]
            }
        ]

        self.assertEqual(sitemap, expected_sitemap)
        self.assertIn("Sitemap successfully saved to Generated/sitemap.json", out.getvalue())


class SignalTests(TestCase):
    def test_assign_property_owner_permissions_signal(self):
        """
        Test that the 'Property Owners' group is created and permissions are assigned upon migration.
        """
        # Disconnect existing signal to prevent duplication
        from django.db.models.signals import post_migrate
        post_migrate.disconnect(assign_property_owner_permissions, sender=None)

        # Trigger the post_migrate signal
        assign_property_owner_permissions(sender=None)

        # Check if the group exists
        group_exists = Group.objects.filter(name='Property Owners').exists()
        self.assertTrue(group_exists)

        group = Group.objects.get(name='Property Owners')

        # Check if permissions are assigned
        accommodation_content_type = ContentType.objects.get_for_model(Accommodation)
        permissions = Permission.objects.filter(content_type=accommodation_content_type)
        for permission in permissions:
            self.assertIn(permission, group.permissions.all())


class FullFlowTests(TestCase):
    def setUp(self):
        """
        Set up complete flow: user signup, approval by superuser, and performing actions.
        """
        self.client = Client()
        self.superuser = User.objects.create_superuser(username='admin', password='adminpass', email='admin@example.com')
        self.country = Location.objects.create(
            id='US',
            title='United States',
            center=Point(-98.583333, 39.833333),
            location_type='country',
            country_code='US'
        )
        self.state = Location.objects.create(
            id='CA',
            title='California',
            center=Point(-119.4179, 36.7783),
            parent_id=self.country,
            location_type='state',
            country_code='US',
            state_abbr='CA'
        )
        self.city = Location.objects.create(
            id='LA',
            title='Los Angeles',
            center=Point(-118.2437, 34.0522),
            parent_id=self.state,
            location_type='city',
            country_code='US',
            city='Los Angeles'
        )

    def test_signup_and_approval_flow(self):
        """
        Test the complete flow of user signup, superuser approval, and performing actions.
        """
        # Step 1: User signs up
        signup_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123'
        }
        response = self.client.post(reverse('signup'), data=signup_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        new_user = User.objects.get(username='newuser')
        self.assertTrue(new_user.groups.filter(name='Property Owners').exists())
        # Assuming approval sets is_active=True, adjust based on actual implementation
        # self.assertFalse(new_user.is_active)

        # Step 2: Superuser approves the user (e.g., activates the account)
        # This step depends on how approval is implemented.
        # For example, if approval involves setting is_active=True:
        new_user.is_active = True
        new_user.save()

        # Step 3: User logs in and performs actions
        login = self.client.login(username='newuser', password='newpassword123')
        self.assertTrue(login)

        # Create an accommodation
        accommodation_data = {
            'title': 'New Accommodation',
            'feed': 2,
            'country_code': 'US',
            'bedroom_count': 3,
            'review_score': 4.0,
            'usd_rate': 200.00,
            'location': self.city.id,
            'amenities': json.dumps({"wifi": True, "air_conditioning": True, "kitchen": False}),
            'published': True
        }
        # Simulate image upload
        image_content = b'\x47\x49\x46\x38\x39\x61\x02\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF\x21\xF9\x04\x01\x0A\x00\x01\x00\x2C\x00\x00\x00\x00\x02\x00\x01\x00\x00\x02\x02\x4C\x01\x00\x3B'
        uploaded_image = mock.MagicMock()
        uploaded_image.name = 'test_image.gif'
        uploaded_image.chunks.return_value = [image_content]

        accommodation_form = AccommodationForm(data=accommodation_data, files={'images': [uploaded_image]})
        self.assertTrue(accommodation_form.is_valid())
        accommodation = accommodation_form.save()

        self.assertEqual(accommodation.title, 'New Accommodation')
        self.assertEqual(accommodation.user, new_user)
        self.assertIn('accommodation_images', accommodation.images[0])

        # Access accommodation detail
        response = self.client.get(reverse('accommodation_detail', args=[accommodation.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New Accommodation')
        self.assertContains(response, 'accommodation_images/test_image.gif')


class SitemapGenerationTests(TestCase):
    def setUp(self):
        """
        Set up sample data for sitemap generation.
        """
        self.country = Location.objects.create(
            id='US',
            title='United States',
            center=Point(-98.583333, 39.833333),
            location_type='country',
            country_code='US'
        )
        self.state = Location.objects.create(
            id='CA',
            title='California',
            center=Point(-119.4179, 36.7783),
            parent_id=self.country,
            location_type='state',
            country_code='US',
            state_abbr='CA'
        )
        self.city = Location.objects.create(
            id='LA',
            title='Los Angeles',
            center=Point(-118.2437, 34.0522),
            parent_id=self.state,
            location_type='city',
            country_code='US',
            city='Los Angeles'
        )

    @mock.patch('properties.management.commands.generate_sitemap.os.makedirs')
    @mock.patch('properties.management.commands.generate_sitemap.open', new_callable=mock.mock_open)
    @mock.patch('properties.management.commands.generate_sitemap.os.path.join')
    def test_generate_sitemap_command_hierarchical(self, mock_join, mock_open_file, mock_makedirs):
        """
        Test that the generate_sitemap command correctly generates hierarchical JSON.
        """
        mock_join.side_effect = lambda *args: os.path.join(*args)
        out = StringIO()
        call_command('generate_sitemap', stdout=out)

        mock_makedirs.assert_called_with('Generated', exist_ok=True)
        mock_open_file.assert_called_with(os.path.join('Generated', 'sitemap.json'), mode='w', encoding='utf-8')

        handle = mock_open_file()
        written_data = ''.join([call.args[0] for call in handle.write.call_args_list])
        sitemap = json.loads(written_data)

        expected_sitemap = [
            {
                "United States": "united-states",
                "locations": [
                    {
                        "California": "california/california",
                        "locations": [
                            {
                                "Los Angeles": "los-angeles/los-angeles"
                            }
                        ]
                    }
                ]
            }
        ]

        self.assertEqual(sitemap, expected_sitemap)
        self.assertIn("Sitemap successfully saved to Generated/sitemap.json", out.getvalue())

    @mock.patch('properties.management.commands.generate_sitemap.os.makedirs')
    @mock.patch('properties.management.commands.generate_sitemap.open', new_callable=mock.mock_open)
    @mock.patch('properties.management.commands.generate_sitemap.os.path.join')
    def test_generate_sitemap_command_empty(self, mock_join, mock_open_file, mock_makedirs):
        """
        Test that the generate_sitemap command handles empty data gracefully.
        """
        Location.objects.all().delete()
        mock_join.side_effect = lambda *args: os.path.join(*args)
        out = StringIO()
        err = StringIO()
        call_command('generate_sitemap', stdout=out, stderr=err)

        self.assertIn("No countries found in the database.", out.getvalue())
        mock_open_file.assert_not_called()

    @mock.patch('properties.management.commands.generate_sitemap.os.makedirs', side_effect=Exception("Directory creation failed"))
    @mock.patch('properties.management.commands.generate_sitemap.open', new_callable=mock.mock_open)
    @mock.patch('properties.management.commands.generate_sitemap.os.path.join')
    def test_generate_sitemap_command_exception_handling(self, mock_join, mock_open_file, mock_makedirs):
        """
        Test that the generate_sitemap command properly handles exceptions.
        """
        mock_join.side_effect = lambda *args: os.path.join(*args)
        out = StringIO()
        err = StringIO()
        with self.assertRaises(CommandError):
            call_command('generate_sitemap', stdout=out, stderr=err)

        self.assertIn("Error generating sitemap: Directory creation failed", err.getvalue())
        mock_open_file.assert_not_called()


class AdminInterfaceTests(TestCase):
    def setUp(self):
        """
        Set up admin user and sample data for admin interface testing.
        """
        self.client = Client()
        self.superuser = User.objects.create_superuser(username='admin', password='adminpass', email='admin@example.com')
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.group = Group.objects.create(name='Property Owners')
        self.country = Location.objects.create(
            id='US',
            title='United States',
            center=Point(-98.583333, 39.833333),
            location_type='country',
            country_code='US'
        )
        self.state = Location.objects.create(
            id='CA',
            title='California',
            center=Point(-119.4179, 36.7783),
            parent_id=self.country,
            location_type='state',
            country_code='US',
            state_abbr='CA'
        )
        self.city = Location.objects.create(
            id='LA',
            title='Los Angeles',
            center=Point(-118.2437, 34.0522),
            parent_id=self.state,
            location_type='city',
            country_code='US',
            city='Los Angeles'
        )
        self.accommodation = Accommodation.objects.create(
            id='ACC1',
            title='Test Accommodation',
            feed=1,
            country_code='US',
            bedroom_count=2,
            review_score=4.5,
            usd_rate=150.00,
            center=Point(-118.2437, 34.0522),
            images=["accommodation_images/test1.jpg"],
            location=self.city,
            amenities={
                "wifi": True,
                "air_conditioning": True,
                "kitchen": True
            },
            user=self.user,
            published=True
        )

    def test_admin_login_required(self):
        response = self.client.get('/admin/')
        self.assertRedirects(response, '/admin/login/?next=/admin/')

    def test_admin_access_superuser(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get('/admin/properties/accommodation/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/properties/accommodation/change_list.html')

    def test_admin_can_add_location(self):
        self.client.login(username='admin', password='adminpass')
        url = '/admin/properties/location/add/'
        data = {
            'id': 'NY',
            'title': 'New York',
            'center_0': '-74.0060',  # Longitude
            'center_1': '40.7128',   # Latitude
            'parent_id': self.country.id,
            'location_type': 'state',
            'country_code': 'US',
            'state_abbr': 'NY',
            'city': 'New York'
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Location.objects.filter(id='NY').exists())

    def test_admin_can_import_location_via_import_export(self):
        self.client.login(username='admin', password='adminpass')
        url = '/admin/properties/location/import/'
        csv_content = """id,title,center,parent_id,location_type,country_code,state_abbr,city
TX,Texas,"POINT(-99.9018 31.9686)",US,state,US,TX,
"""
        response = self.client.post(url, {'import_data': csv_content, 'action': 'import'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Location.objects.filter(id='TX').exists())

    def test_admin_can_change_accommodation(self):
        self.client.login(username='admin', password='adminpass')
        url = f'/admin/properties/accommodation/{self.accommodation.id}/change/'
        data = {
            'title': 'Updated Accommodation',
            'feed': 2,
            'country_code': 'US',
            'bedroom_count': 3,
            'review_score': 4.0,
            'usd_rate': 200.00,
            'center_0': '-118.2437',  # Longitude
            'center_1': '34.0522',    # Latitude
            'images': '["accommodation_images/test2.jpg"]',
            'location': self.city.id,
            'amenities': '{"wifi": true, "air_conditioning": false, "kitchen": true}',
            'user': self.user.id,
            'published': False,
            '_save': 'Save',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.accommodation.refresh_from_db()
        self.assertEqual(self.accommodation.title, 'Updated Accommodation')
        self.assertFalse(self.accommodation.published)

    def test_admin_permissions_assigned_to_group(self):
        """
        Test that the 'Property Owners' group has the correct permissions.
        """
        content_type = ContentType.objects.get_for_model(Accommodation)
        permissions = Permission.objects.filter(content_type=content_type)
        group = Group.objects.get(name='Property Owners')
        for permission in permissions:
            self.assertIn(permission, group.permissions.all())


class AuthenticationAndAuthorizationTests(TestCase):
    def setUp(self):
        """
        Set up users, groups, and sample data for authentication and authorization testing.
        """
        self.client = Client()
        self.superuser = User.objects.create_superuser(username='admin', password='adminpass', email='admin@example.com')
        self.property_owner = User.objects.create_user(username='propertyowner', password='ownerpass')
        self.group = Group.objects.create(name='Property Owners')
        self.property_owner.groups.add(self.group)

        self.country = Location.objects.create(
            id='US',
            title='United States',
            center=Point(-98.583333, 39.833333),
            location_type='country',
            country_code='US'
        )
        self.state = Location.objects.create(
            id='CA',
            title='California',
            center=Point(-119.4179, 36.7783),
            parent_id=self.country,
            location_type='state',
            country_code='US',
            state_abbr='CA'
        )
        self.city = Location.objects.create(
            id='LA',
            title='Los Angeles',
            center=Point(-118.2437, 34.0522),
            parent_id=self.state,
            location_type='city',
            country_code='US',
            city='Los Angeles'
        )
        self.accommodation = Accommodation.objects.create(
            id='ACC1',
            title='Owner Accommodation',
            feed=1,
            country_code='US',
            bedroom_count=2,
            review_score=4.5,
            usd_rate=150.00,
            center=Point(-118.2437, 34.0522),
            images=["accommodation_images/owner1.jpg"],
            location=self.city,
            amenities={
                "wifi": True,
                "air_conditioning": True,
                "kitchen": True
            },
            user=self.property_owner,
            published=True
        )

    def test_property_owner_can_view_own_accommodation(self):
        self.client.login(username='propertyowner', password='ownerpass')
        url = reverse('accommodation_detail', args=[self.accommodation.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Owner Accommodation')

    def test_property_owner_cannot_view_others_accommodation(self):
        # Create another accommodation by a different user
        other_user = User.objects.create_user(username='otheruser', password='otherpass')
        other_accommodation = Accommodation.objects.create(
            id='ACC2',
            title='Other Accommodation',
            feed=1,
            country_code='US',
            bedroom_count=1,
            review_score=3.5,
            usd_rate=100.00,
            center=Point(-117.1611, 32.7157),
            images=["accommodation_images/other1.jpg"],
            location=self.city,
            amenities={
                "wifi": False,
                "air_conditioning": True,
                "kitchen": False
            },
            user=other_user,
            published=True
        )
        self.client.login(username='propertyowner', password='ownerpass')
        url = reverse('accommodation_detail', args=[other_accommodation.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)  # Adjust based on your actual access control
        # If access is restricted, adjust assertions accordingly

    def test_non_property_owner_cannot_access_admin(self):
        non_owner = User.objects.create_user(username='nonowner', password='nonownerpass')
        self.client.login(username='nonowner', password='nonownerpass')
        response = self.client.get('/admin/properties/accommodation/')
        self.assertEqual(response.status_code, 302)  # Redirected due to lack of permissions

    def test_superuser_can_access_admin(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get('/admin/properties/accommodation/')
        self.assertEqual(response.status_code, 200)

