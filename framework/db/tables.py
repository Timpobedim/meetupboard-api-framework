"""Таблицы MeetupBoard. Имена — по соглашениям Django: <приложение>_<модель>."""

from pypika import Table

users = Table("accounts_user")
# ManyToMany «на себя»: profile.followers.add(user) пишет from_user = profile, to_user = подписчик.
followers = Table("accounts_user_followers")
events = Table("events_event")
tags = Table("events_tag")
event_tags = Table("events_event_tags")
attendees = Table("events_event_attendees")
comments = Table("comments_comment")
