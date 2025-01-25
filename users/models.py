from django.db import models
from django.contrib.auth.models import AbstractUser
from PIL import Image

from django.contrib.auth import get_user_model
User = get_user_model()

class Profile(models.Model):
    """This model extends Django User model with a profile picture.

    """
    # one-to-one mapping with Django User model
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # profile picture for each user
    avatar = models.ImageField(default='default.jpg', upload_to='profile_images')
    
    def __str__(self):
        """This function returns user's name.

        Returns:
            str: name of user
        """
        return self.user.name

    def save(self, *args, **kwargs):
        """This function resize and save the image on saving user's data.
        """
        super().save()

        # open profile pic
        img = Image.open(self.avatar.path)

        # size check
        if img.height > 100 or img.width > 100:
            new_img = (100, 100)
            img.thumbnail(new_img)
            # save image
            img.save(self.avatar.path)