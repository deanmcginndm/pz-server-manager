from django.db import models


class Localplayers(models.Model):
    name = models.TextField(blank=True, null=True)  # This field type is a guess.
    wx = models.IntegerField(blank=True, null=True)
    wy = models.IntegerField(blank=True, null=True)
    x = models.TextField(blank=True, null=True)  # This field type is a guess.
    y = models.TextField(blank=True, null=True)  # This field type is a guess.
    z = models.TextField(blank=True, null=True)  # This field type is a guess.
    worldversion = models.IntegerField(blank=True, null=True)
    data = models.BinaryField(blank=True, null=True)
    isdead = models.BooleanField(db_column='isDead', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'localPlayers'


class RawBinaryField(models.BinaryField):
    def value_to_string(self, obj):
        """Binary data is serialized as base64"""
        return self.value_from_object(obj)

    def to_python(self, value):
        # If it's a string, it should be base64-encoded data
        if isinstance(value, str):
            return value.encode('ascii')
        return value


class Networkplayers(models.Model):
    world = models.TextField(blank=True, null=True)
    username = models.TextField(blank=True, null=True)
    playerindex = models.IntegerField(db_column='playerIndex', blank=True, null=True)  # Field name made lowercase.
    name = models.TextField(blank=True, null=True)  # This field type is a guess.
    steamid = models.TextField(blank=True, null=True)  # This field type is a guess.
    x = models.TextField(blank=True, null=True)  # This field type is a guess.
    y = models.TextField(blank=True, null=True)  # This field type is a guess.
    z = models.TextField(blank=True, null=True)  # This field type is a guess.
    worldversion = models.IntegerField(blank=True, null=True)
    data = RawBinaryField(blank=True, null=True)
    isdead = models.BooleanField(db_column='isDead', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'networkPlayers'


class Bannedid(models.Model):
    steamid = models.TextField()
    reason = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bannedid'




class Bannedip(models.Model):
    ip = models.TextField()
    username = models.TextField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bannedip'


class Tickets(models.Model):
    message = models.TextField()
    author = models.TextField()
    answeredid = models.IntegerField(db_column='answeredID', blank=True, null=True)  # Field name made lowercase.
    viewed = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tickets'


class Userlog(models.Model):
    username = models.TextField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    issuedby = models.TextField(db_column='issuedBy', blank=True, null=True)  # Field name made lowercase.
    amount = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'userlog'


class Whitelist(models.Model):
    world = models.TextField(blank=True, null=True)
    username = models.TextField(unique=True, blank=True, null=True)
    password = models.TextField(blank=True, null=True)
    admin = models.BooleanField(blank=True, null=True)
    moderator = models.BooleanField(blank=True, null=True)
    banned = models.BooleanField(blank=True, null=True)
    priority = models.BooleanField(blank=True, null=True)
    lastconnection = models.TextField(db_column='lastConnection', blank=True, null=True)  # Field name made lowercase.
    encryptedpwd = models.BooleanField(db_column='encryptedPwd', blank=True, null=True)  # Field name made lowercase.
    pwdencrypttype = models.IntegerField(db_column='pwdEncryptType', blank=True, null=True)  # Field name made lowercase.
    steamid = models.TextField(blank=True, null=True)
    ownerid = models.TextField(blank=True, null=True)
    accesslevel = models.TextField(blank=True, null=True)
    transactionid = models.IntegerField(db_column='transactionID', blank=True, null=True)  # Field name made lowercase.
    displayname = models.TextField(db_column='displayName', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'whitelist'

Localplayers.objects = Localplayers.objects.using('players')
Networkplayers.objects = Networkplayers.objects.using('players')
Bannedid.objects = Bannedid.objects.using('game')
Bannedip.objects = Bannedip.objects.using('game')
Tickets.objects = Tickets.objects.using('game')
Userlog.objects = Userlog.objects.using('game')
Whitelist.objects = Whitelist.objects.using('game')