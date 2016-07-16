import datetime
import re

from django.conf import settings
from django.db import models
from django.db.transaction import atomic as atomic_decorator
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.utils.timezone import now as datetime_now
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string

SHA1_RE = re.compile('^[a-f0-9]{40}$')


class RegistrationProfile(models.Model):
    """
    A simple profile which stores an activation key for use during
    user account registration.
    """
    ACTIVATED = u"ALREADY_ACTIVATED"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        unique=True,
        verbose_name=_('user'),
        related_name='api_registration_profile'
    )
    activation_key = models.CharField(_('activation key'), max_length=40)

    def activation_key_expired(self):
        """
        Determine whether this ``RegistrationProfile``'s activation
        key has expired, returning a boolean -- ``True`` if the key
        has expired.
        Key expiration is determined by a two-step process:
        1. If the user has already activated, the key will have been
        reset to the string constant ``ACTIVATED``. Re-activating
        is not permitted, and so this method returns ``True`` in
        this case.
        2. Otherwise, the date the user signed up is incremented by
        the number of days specified in the setting
        ``REGISTRATION_API_ACCOUNT_ACTIVATION_DAYS`` (which should be
        the number of days after signup during which a user is allowed
        to activate their account); if the result is less than or
        equal to the current date, the key has expired and this method
        returns ``True``.
        """

        expiration_date = datetime.timedelta(days=30)
        return self.activation_key == self.ACTIVATED or \
            (self.user.date_joined + expiration_date <= datetime_now())

    @classmethod
    def create_inactive(cls, username=None, email=None, password=None, **kwargs):
        user_model = get_user_model()
        if username is not None:
            new_user = user_model.objects.create_user(username, email, password)
        else:
            new_user = user_model.objects.create_user(email=email, password=password)
        new_user.is_active = False
        new_user.save()
        cls.create_profile(new_user)
        site = Site.objects.get_current()
        send_activation_email(new_user, site)
        return new_user


    @classmethod
    def activate_user(cls, activation_key):
        """
        Validate an activation key and activate the corresponding
        ``User`` if valid.
        If the key is valid and has not expired, return the ``User``
        after activating.
        If the key is not valid or has expired, return ``False``.
        If the key is valid but the ``User`` is already active,
        return ``False``.
        To prevent reactivation of an account which has been
        deactivated by site administrators, the activation key is
        reset to the string constant ``RegistrationProfile.ACTIVATED``
        after successful activation.
        """
        # Make sure the key we're trying conforms to the pattern of a
        # SHA1 hash; if it doesn't, no point trying to look it up in
        # the database.
        if SHA1_RE.search(activation_key):
            try:
                profile = cls.objects.get(
                    activation_key=activation_key)
            except cls.DoesNotExist:
                return False
            if not profile.activation_key_expired():
                user = profile.user
                user.is_active = True
                user.save()
                profile.activation_key = cls.ACTIVATED
                profile.save()
                return user
        return False

    @classmethod
    def create_profile(cls, user):
        activation_key = create_activation_key(user)
        registration_profile = cls.objects.create(
            user=user, activation_key=activation_key)
        return registration_profile


def create_activation_key(user):
    username = getattr(user, user.USERNAME_FIELD)
    salt_bytes = str(random.random()).encode('utf-8')
    salt = hashlib.sha1(salt_bytes).hexdigest()[:5]

    hash_input = (salt + username).encode('utf-8')
    activation_key = hashlib.sha1(hash_input).hexdigest()
    return activation_key


def send_activation_email(user, site):
    """
    Send an activation email to the ``user``.
    The activation email will make use of two templates:
    ``registration/activation_email_subject.txt``
    This template will be used for the subject line of the
    email. Because it is used as the subject line of an email,
    this template's output **must** be only a single line of
    text; output longer than one line will be forcibly joined
    into only a single line.
    ``registration/activation_email.txt``
    This template will be used for the body of the email.
    These templates will each receive the following context
    variables:
    ``activation_key``
    The activation key for the new account.
    ``expiration_days``
    The number of days remaining during which the account may
    be activated.
    ``site``
    An object representing the site on which the user
    registered; depending on whether ``django.contrib.sites``
    is installed, this may be an instance of either
    ``django.contrib.sites.models.Site`` (if the sites
    application is installed) or
    ``django.contrib.sites.models.RequestSite`` (if
    not). Consult the documentation for the Django sites
    framework for details regarding these objects' interfaces.
    """
    ctx_dict = {'activation_link': "http://{0}{1}".format(
                    site.domain,
                    reverse('activate', user.api_registration_profile.activation_key)
                ),
                'expiration_days': 30,
                'site': site}
    subject = "Activate your account on {0}".format(site.domain)
    message = render_to_string('activation.html', ctx_dict)
    user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
