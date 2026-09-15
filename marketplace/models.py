"""
Farmer's Market - core models
app: marketplace/models.py

Notes for the team:
- Each model below maps 1:1 to a box in the ER diagram.
- Money fields use DecimalField, never FloatField (avoids rounding errors on settlement).
- Uses Django's built-in User model for auth; Farmer/Consumer extend it via OneToOne.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class Hub(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Farmer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, unique=True)
    village = models.CharField(max_length=150)
    id_proof = models.FileField(upload_to="farmer_docs/")
    land_proof = models.FileField(upload_to="farmer_docs/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({'verified' if self.is_verified else 'pending'})"


class Consumer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, unique=True)
    hub = models.ForeignKey(Hub, on_delete=models.SET_NULL, null=True, related_name="consumers")

    def __str__(self):
        return self.name


class WeeklyCycle(models.Model):
    """One row per week. Drives the whole pre-order timeline."""
    order_open = models.DateField()      # Monday
    order_close = models.DateTimeField() # Tuesday evening
    pickup_date = models.DateField()     # Thursday
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Cycle {self.order_open} to {self.pickup_date}"


class Listing(models.Model):
    """A farmer's produce offer for a specific weekly cycle."""
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name="listings")
    cycle = models.ForeignKey(WeeklyCycle, on_delete=models.CASCADE, related_name="listings")
    produce_name = models.CharField(max_length=100)
    price_per_kg = models.DecimalField(max_digits=8, decimal_places=2,
                                        validators=[MinValueValidator(0)])
    quantity_available = models.DecimalField(max_digits=8, decimal_places=2,
                                              validators=[MinValueValidator(0)])
    quantity_sold = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        unique_together = ("farmer", "cycle", "produce_name")

    def __str__(self):
        return f"{self.produce_name} - {self.farmer.name} ({self.cycle})"

    @property
    def quantity_remaining(self):
        return self.quantity_available - self.quantity_sold


class Order(models.Model):
    STATUS_CHOICES = [
        ("placed", "Placed"),
        ("harvested", "Harvested"),
        ("ready", "Ready for pickup"),
        ("collected", "Collected"),
        ("cancelled", "Cancelled"),
    ]
    PAYMENT_CHOICES = [
        ("online", "Online (Razorpay)"),
        ("cash", "Cash at hub"),
    ]

    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name="orders")
    hub = models.ForeignKey(Hub, on_delete=models.CASCADE, related_name="orders")
    cycle = models.ForeignKey(WeeklyCycle, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="placed")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default="online")
    payment_id = models.CharField(max_length=100, blank=True, null=True)  # Razorpay payment id
    pickup_otp = models.CharField(max_length=6, blank=True, null=True)
    placed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.consumer.name}"

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    listing = models.ForeignKey(Listing, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.DecimalField(max_digits=8, decimal_places=2,
                                    validators=[MinValueValidator(0.1)])
    # snapshot the price at order time so later price changes don't affect past orders
    price_locked = models.DecimalField(max_digits=8, decimal_places=2)

    @property
    def subtotal(self):
        return self.quantity * self.price_locked

    def __str__(self):
        return f"{self.quantity}kg {self.listing.produce_name} (order #{self.order_id})"


class Settlement(models.Model):
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name="settlements")
    cycle = models.ForeignKey(WeeklyCycle, on_delete=models.CASCADE, related_name="settlements")
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_rate = models.DecimalField(max_digits=4, decimal_places=2, default=5.00)  # in %
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    net_payable = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("farmer", "cycle")

    def save(self, *args, **kwargs):
        # keep commission/net in sync if gross or rate changes
        self.commission_amount = self.gross_amount * (self.commission_rate / 100)
        self.net_payable = self.gross_amount - self.commission_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Settlement for {self.farmer.name} - {self.cycle}"
