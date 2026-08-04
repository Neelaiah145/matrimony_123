from datetime import date
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q

from apps.accounts.models import User
from .models import ProfileMatch, Interest, BlockedProfile, Shortlist, IgnoredProfile


class MatchService:
    """ Partner Matching Service """
    # Calculate Age

    def calculate_age(self, dob):

        if not dob:
            return None

        today = date.today()

        return (
            today.year
            - dob.year
            - (
                (today.month, today.day)
                < (dob.month, dob.day)
            )
        )

    # Age Score
   
    def age_score(self, age, minimum_age, maximum_age):

        if age is None:
            return 0

        if minimum_age <= age <= maximum_age:
            return 20

        if age == minimum_age - 1 or age == maximum_age + 1:
            return 15

        if age == minimum_age - 2 or age == maximum_age + 2:
            return 10

        return 0

   
    # Height Score
    def height_score(self, height, minimum_height, maximum_height):

        height = Decimal(height)

        if minimum_height <= height <= maximum_height:
            return 15

        if (
            minimum_height - Decimal("0.10")
            <= height
            <= maximum_height + Decimal("0.10")
        ):
            return 12

        if (
            minimum_height - Decimal("0.20")
            <= height
            <= maximum_height + Decimal("0.20")
        ):
            return 8

        return 0

    # Salary Score
    
    def salary_score(self,salary,minimum_salary,maximum_salary,):

        if salary is None:
            return 0

        if (
            minimum_salary is None
            or maximum_salary is None
        ):
            return 10

        if minimum_salary <= salary <= maximum_salary:
            return 10

        if (
            minimum_salary - Decimal("10000")
            <= salary
            <= maximum_salary + Decimal("10000")
        ):
            return 8

        if (
            minimum_salary - Decimal("20000")
            <= salary
            <= maximum_salary + Decimal("20000")
        ):
            return 5

        return 0

    # Get Candidates
    def get_candidates(self, user):

        if not hasattr(user, "partner_preference"):
            return User.objects.none()

        preference = user.partner_preference

        target_gender = (
            "FEMALE"
            if user.gender == "MALE"
            else "MALE"
        )

        candidates = (
            User.objects.filter(
                gender=target_gender,
                is_active=True,
                profile__isnull=False,
                partner_preference__isnull=False,
            )
            .exclude(id=user.id)
            .select_related(
                "profile",
                "partner_preference",
            )
        )


        if preference.country:
            candidates = candidates.filter(
                profile__country__iexact=preference.country
            )

        return candidates
    # Match Score
    
    def calculate_match_score(self, user, candidate):

        preference = user.partner_preference
        profile = candidate.profile

        score = 0
        matched_fields = []
        age = self.calculate_age(candidate.date_of_birth)

        age_points = self.age_score(
            age,
            preference.minimum_age,
            preference.maximum_age,
        )

        if age_points:
            score += age_points
            matched_fields.append("Age")

     
        height_points = self.height_score(
            profile.height,
            preference.minimum_height,
            preference.maximum_height,
        )

        if height_points:
            score += height_points
            matched_fields.append("Height")


        if preference.religion:

            if (
                profile.religion
                and profile.religion.lower()
                == preference.religion.lower()
            ):
                score += 15
                matched_fields.append("Religion")

        else:
            score += 15

        if preference.caste:

            if (
                profile.caste
                and profile.caste.lower()
                == preference.caste.lower()
            ):
                score += 10
                matched_fields.append("Caste")

        else:
            score += 10

        if preference.education:

            if (
                profile.highest_education
                and profile.highest_education.lower()
                == preference.education.lower()
            ):
                score += 10
                matched_fields.append("Education")

        else:
            score += 10

        if preference.profession:

            if (
                profile.occupation
                and profile.occupation.lower()
                == preference.profession.lower()
            ):
                score += 10
                matched_fields.append("Profession")

        else:
            score += 10

        salary_points = self.salary_score(
            profile.annual_income,
            preference.minimum_salary,
            preference.maximum_salary,
        )

        if salary_points:
            score += salary_points
            matched_fields.append("Salary")

        if (
            preference.country
            and profile.country
            and profile.country.lower()
            == preference.country.lower()
        ):
            score += 5
            matched_fields.append("Country")


        if (
            preference.state
            and profile.state
            and profile.state.lower()
            == preference.state.lower()
        ):
            score += 3
            matched_fields.append("State")


        if (
            preference.city
            and profile.city
            and profile.city.lower()
            == preference.city.lower()
        ):
            score += 2
            matched_fields.append("City")

       

        if preference.diet and profile.diet:
            if profile.diet.lower() == preference.diet.lower():
                score += 2
                matched_fields.append("Diet")


        if preference.smoking and profile.smoking:
            if profile.smoking.lower() == preference.smoking.lower():
                score += 2
                matched_fields.append("Smoking")


        if preference.drinking and profile.drinking:
            if profile.drinking.lower() == preference.drinking.lower():
                score += 1
                matched_fields.append("Drinking")


        if (
            preference.horoscope_preferences
            and hasattr(profile, "horoscope")
            and profile.horoscope
        ):

            if (
                profile.horoscope.lower()
                == preference.horoscope_preferences.lower()
            ):
                score += 5
                matched_fields.append("Horoscope")

        return score, matched_fields

    
    # Save Match
  

    def save_match(self, user, candidate, score, matched_fields):

        match, created = ProfileMatch.objects.update_or_create(
            from_user=user,
            to_user=candidate,
            defaults={
                "match_percentage": score,
                "matched_fields": matched_fields,
            },
        )

        return match

   
    # Mutual Match
    

    def check_mutual_match(self, user, candidate):

        return ProfileMatch.objects.filter(
            from_user=candidate,
            to_user=user,
        ).exists()


    # Recalculate Matches
    

    def recalculate_matches(self, user):

        ProfileMatch.objects.filter(
            from_user=user
        ).delete()

        candidates = self.get_candidates(user)

        results = []

        for candidate in candidates:

            score, matched_fields = self.calculate_match_score(
                user,
                candidate,
            )

       
            if score < 40:
                continue

            match = self.save_match(
                user=user,
                candidate=candidate,
                score=score,
                matched_fields=matched_fields,
            )

            if self.check_mutual_match(user, candidate):

                match.is_mutual = True
                match.save(update_fields=["is_mutual"])

                ProfileMatch.objects.filter(
                    from_user=candidate,
                    to_user=user,
                ).update(is_mutual=True)

            results.append(match)

        return results

    
    # Recommendations
   

    def get_recommendations(self, user, limit=20):

        if not ProfileMatch.objects.filter(
            from_user=user
        ).exists():
            self.recalculate_matches(user)

        return (
            ProfileMatch.objects.filter(
                from_user=user
            )
            .select_related(
                "to_user",
                "to_user__profile",
            )
            .order_by("-match_percentage")[:limit]
        )


class InterestService:
    """
    Service to handle user expressions of interest.
    """

    def send_interest(self, from_user, to_user, message=None):
        """
        Send an interest expression from one user to another.
        Checks for self-interest, blocks, duplicates, and opposite pending interests.
        """
        if from_user == to_user:
            raise ValidationError("You cannot send an interest to yourself.")

        is_blocked = BlockedProfile.objects.filter(
            Q(from_user=from_user, to_user=to_user) |
            Q(from_user=to_user, to_user=from_user)
        ).exists()
        if is_blocked:
            raise ValidationError("Cannot send interest. One of the profiles has blocked the other.")

        
        incoming_interest = Interest.objects.filter(from_user=to_user, to_user=from_user).first()
        if incoming_interest and incoming_interest.status == Interest.Status.PENDING:
            raise ValidationError("This profile has already sent you an interest. Please accept it instead.")

      
        interest = Interest.objects.filter(from_user=from_user, to_user=to_user).first()
        if interest:
            if interest.status in [Interest.Status.PENDING, Interest.Status.ACCEPTED]:
                raise ValidationError("An active interest already exists between you and this profile.")
            
            interest.status = Interest.Status.PENDING
            interest.message = message
            interest.is_seen = False
            interest.withdrawn_at = None
            interest.rejected_at = None
            interest.accepted_at = None
            interest.responded_at = None
            interest.save()
        else:
            interest = Interest.objects.create(
                from_user=from_user,
                to_user=to_user,
                message=message,
                status=Interest.Status.PENDING
            )

        self._trigger_notification(interest, "SENT")
        return interest

    def get_sent_interests(self, user):
        """
        Retrieve all interests sent by a user.
        """
        return Interest.objects.filter(from_user=user).select_related("to_user", "to_user__profile")

    def get_received_interests(self, user):
        """
        Retrieve all active interests received by a user.
        """
        return Interest.objects.filter(to_user=user).exclude(
            status=Interest.Status.WITHDRAWN
        ).select_related("from_user", "from_user__profile")

    def accept_interest(self, interest_id, user):
        """
        Accept an interest expression. Only the recipient can accept.
        """
        try:
            interest = Interest.objects.get(id=interest_id, to_user=user)
        except Interest.DoesNotExist:
            raise ValidationError("Interest request not found.")

        if interest.status != Interest.Status.PENDING:
            raise ValidationError(f"Cannot accept interest with status {interest.status}.")

        interest.status = Interest.Status.ACCEPTED
        interest.is_seen = True
        interest.accepted_at = timezone.now()
        interest.responded_at = timezone.now()
        interest.save()

        
        try:
            from apps.chat.services import ChatRoomService
            ChatRoomService.get_or_create_room(interest.from_user, interest.to_user)
        except Exception:
            pass

        self._trigger_notification(interest, "ACCEPTED")
        return interest

    def reject_interest(self, interest_id, user):
        """
        Reject an interest expression. Only the recipient can reject.
        """
        try:
            interest = Interest.objects.get(id=interest_id, to_user=user)
        except Interest.DoesNotExist:
            raise ValidationError("Interest request not found.")

        if interest.status != Interest.Status.PENDING:
            raise ValidationError(f"Cannot reject interest with status {interest.status}.")

        interest.status = Interest.Status.REJECTED
        interest.is_seen = True
        interest.rejected_at = timezone.now()
        interest.responded_at = timezone.now()
        interest.save()

        self._trigger_notification(interest, "REJECTED")
        return interest

    def withdraw_interest(self, interest_id, user):
        """
        Withdraw a sent interest expression. Only the sender can withdraw.
        """
        try:
            interest = Interest.objects.get(id=interest_id, from_user=user)
        except Interest.DoesNotExist:
            raise ValidationError("Interest request not found.")

        if interest.status != Interest.Status.PENDING:
            raise ValidationError(f"Cannot withdraw interest with status {interest.status}.")

        interest.status = Interest.Status.WITHDRAWN
        interest.withdrawn_at = timezone.now()
        interest.save()

        self._trigger_notification(interest, "WITHDRAWN")
        return interest

    def delete_interest(self, interest_id, user):
        """
        Delete/remove an interest record. Either the sender or receiver can delete.
        """
        try:
            interest = Interest.objects.get(
                Q(from_user=user) | Q(to_user=user),
                id=interest_id
            )
        except Interest.DoesNotExist:
            raise ValidationError("Interest request not found.")

        interest.delete()
        return True

    def _trigger_notification(self, interest, action_type):
        """
        Hook to trigger notifications when an interest event occurs.
        """
        pass


class ShortlistService:
    """
    Service to handle user shortlists.
    """

    def add_to_shortlist(self, owner, shortlisted_user):
        """
        Add a profile to user's shortlist.
        """
        if owner == shortlisted_user:
            raise ValidationError("You cannot shortlist yourself.")


        is_blocked = BlockedProfile.objects.filter(
            Q(from_user=owner, to_user=shortlisted_user) |
            Q(from_user=shortlisted_user, to_user=owner)
        ).exists()
        if is_blocked:
            raise ValidationError("Cannot shortlist. One of the profiles has blocked the other.")

        shortlist, created = Shortlist.objects.get_or_create(
            owner=owner,
            shortlisted_user=shortlisted_user
        )
        return shortlist

    def get_shortlisted_profiles(self, owner):
        """
        Retrieve all profiles shortlisted by owner.
        """
        return Shortlist.objects.filter(owner=owner).select_related(
            "shortlisted_user",
            "shortlisted_user__profile"
        )

    def remove_from_shortlist(self, owner, shortlisted_user):
        """
        Remove a profile from user's shortlist.
        """
        try:
            shortlist = Shortlist.objects.get(owner=owner, shortlisted_user=shortlisted_user)
            shortlist.delete()
            return True
        except Shortlist.DoesNotExist:
            raise ValidationError("Profile is not shortlisted.")


class IgnoreService:
    """
    Service to ignore profiles from recommendations.
    """

    def ignore_profile(self, from_user, to_user):
        """
        Ignore a user profile.
        """
        if from_user == to_user:
            raise ValidationError("You cannot ignore yourself.")

        ignored, created = IgnoredProfile.objects.get_or_create(
            from_user=from_user,
            to_user=to_user
        )
        return ignored

    def get_ignored_profiles(self, from_user):
        """
        Retrieve all profiles ignored by user.
        """
        return IgnoredProfile.objects.filter(from_user=from_user).select_related(
            "to_user",
            "to_user__profile"
        )

    def remove_ignored_profile(self, from_user, to_user):
        """
        Remove a profile from ignored list.
        """
        try:
            ignored = IgnoredProfile.objects.get(from_user=from_user, to_user=to_user)
            ignored.delete()
            return True
        except IgnoredProfile.DoesNotExist:
            raise ValidationError("Profile is not ignored.")


class BlockService:
    """
    Service to block user profiles.
    """

    def block_profile(self, from_user, to_user):
        """
        Block a profile. Automatically removes shortlists and handles active interests.
        """
        if from_user == to_user:
            raise ValidationError("You cannot block yourself.")

        blocked, created = BlockedProfile.objects.get_or_create(
            from_user=from_user,
            to_user=to_user
        )


        Shortlist.objects.filter(
            Q(owner=from_user, shortlisted_user=to_user) |
            Q(owner=to_user, shortlisted_user=from_user)
        ).delete()

        Interest.objects.filter(
            Q(from_user=from_user, to_user=to_user) |
            Q(from_user=to_user, to_user=from_user)
        ).delete()

        return blocked

    def get_blocked_profiles(self, from_user):
        """
        Retrieve all profiles blocked by user.
        """
        return BlockedProfile.objects.filter(from_user=from_user).select_related(
            "to_user",
            "to_user__profile"
        )

    def unblock_profile(self, from_user, to_user):
        """
        Unblock a profile.
        """
        try:
            blocked = BlockedProfile.objects.get(from_user=from_user, to_user=to_user)
            blocked.delete()
            return True
        except BlockedProfile.DoesNotExist:
            raise ValidationError("Profile is not blocked.")
    