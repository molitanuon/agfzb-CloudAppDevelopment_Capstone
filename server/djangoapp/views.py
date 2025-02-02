from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
# from .models import related models
# from .restapis import related methods

from .models import CarModel, CarMake, CarDealer, DealerReview
from .restapis import get_dealers_from_cf, get_dealer_by_id_from_cf, get_dealer_reviews_from_cf, post_request

from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    if request.method == "GET":
        return render(request, 'djangoapp/about.html')


# Create a `contact` view to return a static contact page
def contact(request):
    if request.method == "GET":
        return render(request, 'djangoapp/contact.html')

# Create a `login_request` view to handle sign in request
def login_request(request):
    context={}
    #Handles POST request 
    if request.method == "POST":
        #Get the username and password from request.POST dictoionary 
        username = request.POST['username']
        password = request.POST['psw']
        #Check if given credential can be authenticated 
        user = authenticate(username=username, password=password)
        if user is not None:
            #user valid, call login method to login cur user 
            login(request, user)
            return redirect('djangoapp:index')
        else:
            #if not, return to login page again 
            return render(request, 'djangoapp/user_login.html', context)
    else:
        return render(request, 'djangoapp/user_login.html', context)



# Create a `logout_request` view to handle sign out request
def logout_request(request):
    print("Log out the user `{}`".format(request.user.username))
    logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == "POST":
        #check if user exists 
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try: 
            User.objects.get(username=username)
            user_exist = True
        except: 
            logger.error("New User")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name, password=password)
            login(request, user)
            return redirect("djangoapp:index")
        else: 
            context['message'] = "User already exists."
            return render(request, 'djangoapp/registration.html', context)


# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    context = {}
    if request.method == "GET":
        url = "https://8779b430.us-south.apigw.appdomain.cloud/api/dealership"
        dealerships = get_dealers_from_cf(url)
        context["dealerships"] = dealerships
        # dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
        # return HttpResponse(dealer_names)
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
# def get_dealer_details(request, dealer_id):
# ...
def get_dealer_details(request, dealer_id):
    if request.method == "GET":
        context = {}
        dealer_url = "https://8779b430.us-south.apigw.appdomain.cloud/api/dealership"
        dealer = get_dealer_by_id_from_cf(dealer_url, dealer_id=dealer_id)
        context["dealer"] = dealer
        # context["dealer"].id = dealer_id
        # context["dealer"].full_name = full_name

        review_url = "https://8779b430.us-south.apigw.appdomain.cloud/api/review?dealer_id=" + str(dealer_id)
        reviews = get_dealer_reviews_from_cf(review_url, dealer_id=dealer_id)
        if reviews:
            context["reviews"] = reviews
            return render(request, 'djangoapp/dealer_details.html', context) 
        else:
            return redirect("djangoapp:index")

# Create a `add_review` view to submit a review
# def add_review(request, dealer_id):
# ...
def add_review(request, dealer_id):
    context = {}
    dealer_url = "https://8779b430.us-south.apigw.appdomain.cloud/api/dealership"
    dealer = get_dealer_by_id_from_cf(dealer_url, dealer_id=dealer_id)
    context["dealer"] = dealer 

    if request.method == "GET":
        cars = CarModel.objects.all()
        context["cars"] = cars
        return render(request, 'djangoapp/add_review.html', context)
    
    if request.method == "POST":
        if request.user.is_authenticated:
            username = request.user.username 
            car_id = request.POST["car"]
            car = CarModel.objects.get(pk=car_id)
        
            review = {}
            review["time"] = datetime.utcnow().isoformat()
            review["dealership"] = dealer_id
            review["review"] = request.POST["content"]
            review["name"] = username
            review["purchase"] = False
            review["car_make"] = ""
            review["car_model"] = ""
            review["car_year"] = 0
            review["purchase_date"] = "mm/dd/yy"
            review["id"] = dealer_id

            if "purchasecheck" in request.POST:
                if request.POST["purchasecheck"] == 'on':
                    review["purchase"] = True
                    review["car_make"] = car.car_make.name
                    review["car_model"] = car.name
                    review["car_year"] = int(car.year.strftime("%Y"))
                    review["purchase_date"] = request.POST["purchase_date"]
                    review["id"] = dealer_id
        
            json_payload = {}
            json_payload["review"] = review
            url = "https://8779b430.us-south.apigw.appdomain.cloud/api/reviews"
            post_request(url, json_payload, dealer_id=dealer_id)
    return redirect("djangoapp:dealer_details", dealer_id=dealer_id)
