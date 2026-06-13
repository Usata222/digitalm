from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg


class Product(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    price = models.FloatField()
    file = models.FileField(upload_to='uploads/')
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    total_sales_amount = models.IntegerField(default=0)
    total_sales = models.IntegerField(default=0)
    image = models.ImageField(upload_to='uploads/')

    def __str__(self):
        return self.name

    def average_rating(self):
        result = self.ratings.aggregate(avg=Avg('stars'))
        avg = result['avg']
        return round(avg, 1) if avg else None

    def rating_count(self):
        return self.ratings.count()


class OrderDetail(models.Model):
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    customer_email = models.EmailField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    amount = models.FloatField()
    session_id = models.CharField(max_length=200)
    stripe_payment_intent = models.CharField(max_length=200, null=True, blank=True)
    has_paid = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)


class Rating(models.Model):
    STAR_CHOICES = [(i, i) for i in range(1, 6)]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings')
    stars = models.IntegerField(choices=STAR_CHOICES)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        # One rating per user per product — enforced at DB level
        unique_together = ('user', 'product')

    def __str__(self):
        return f'{self.user.username} rated {self.product.name}: {self.stars}★'
