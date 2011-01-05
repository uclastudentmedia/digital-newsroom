from newsroom_core import models


def get_profile(user):
    """
    Get the newsroom profile for a user. If no profile exists, return an empty
    NewsroomProfile model (so that default settings can be checked against).
    """
    try:
        return user.newsroomprofile
    except models.NewsroomProfile.DoesNotExist:
        return models.NewsroomProfile(user=user)
    except AttributeError:
        # Most likely we're dealing with an AnonymousUser
        return models.NewsroomProfile()
