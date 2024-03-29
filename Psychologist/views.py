from base64 import urlsafe_b64decode
from email.message import EmailMessage
from django.shortcuts import redirect,render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from helo import settings
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from . tokens import generate_token
from Psychologist.models import Contact
from datetime import datetime
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
nltk.download('vader_lexicon')


# Create your views here.



def analyze_sentiment_emotion(request):
    if request.method == 'POST':
        user_text = request.POST.get('user_input', '')
        sia = SentimentIntensityAnalyzer()
        sentiment_scores = sia.polarity_scores(user_text)
        
        # Sentiment analysis
        sentiment = "Neutral"
        if sentiment_scores['compound'] >= 0.05:
            sentiment = "Positive"
        elif sentiment_scores['compound'] <= -0.05:
            sentiment = "Negative"
        
        # Emotion detection (simple rule-based method)
        words = user_text.lower().split()
        emotions = {
            'happy': any(word in words for word in ['happy', 'joy', 'excited', 'glad', 'delighted']),
            'sad': any(word in words for word in ['sad', 'unhappy', 'gloomy', 'miserable']),
            'angry': any(word in words for word in ['angry', 'mad', 'furious', 'irritated']),
            # Add more emotions and related words as needed
        }
        
        # Capitalize emotion names before sending them to the template
        capitalized_emotions = {emotion.capitalize(): detected for emotion, detected in emotions.items()}
        
        return render(request, 'sentiment_emotion_result.html', {'sentiment': sentiment, 'emotions': capitalized_emotions})
    
    return render(request, 'analyze_sentiment_emotion.html')






def home(request):
    return render(request, "index.html")

def signup(request):

    if request.method == 'POST':
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        password = request.POST['password']
        confirmpw = request.POST['confirmpw']

        if User.objects.filter(username = username):
            messages.error(request, "Username already exist! Please try again!!")
            return redirect('home')

        if User.objects.filter(email = email):
            messages.error(request, 'Email already in use')
            return redirect('home')
        
        if len(username)>10:
            messages(request, 'username must be under 10 characters')

        if password != confirmpw:
            messages.error(request, "Password didn't match!")
        
        if not username.isalnum():
            messages.error(request, "Username must be Alpha-Numeric")
            return redirect('home')

        myuser = User.objects.create_user(username, email, password)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = False
        myuser.save()

        messages.success(request, " Your account has been successfully created!! We have sent you a confirmation mail in you email-id")

        #Welcom Email

        subject = "Welcome to Psychologist !!"
        message = "Hello " + myuser.first_name + "!! \n" + "Welcome to Psychologist!! \n Thank you for visiting our website \n. We have also sent you a confirmation email, please confirm your email address. \n\n Thanking You\n Vijaya Mishra"        
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=True)
        
        #Email Address Confirmation Email 

        current_site = get_current_site(request)
        email_subject = "Confirm your email"
        message2 = render_to_string('email_confirmation.html',{
            'name': myuser.first_name,
            'domain':current_site.domain,
            'uid':urlsafe_base64_encode(force_bytes(myuser.pk)),
            'tokens': generate_token.make_token(myuser)
        })
        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],

        )
        email.fail.silentlt = True
        email.send()

        return redirect('signin')

    return render(request, "signup.html")

def signin(request): 

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(username = username, password = password)

        if user is not  None:
            login(request, user)
            fname = user.first_name
            return render(request, 'index.html', {'fname': fname})

        else:
            messages.error(request, "Bad Credentials")
            return redirect('home')
    

    return render(request, "signin.html")

def activate(request , uidb64, token):
    try:
        uid = force_bytes(urlsafe_b64decode(uidb64))
        myuser = User.object.get(pk=uid)
    except(TypeError,ValueError, OverflowError, User.DoesNotExist):
        myuser = None

    if myuser is not None and generate_token.check_token(myuser,token):
        myuser.is_active = True
        myuser.save()
        login(request, myuser)
        return redirect(request, 'activation_failed.html')




def signout(request):
    logout(request)
    messages.success(request, "Logged Out Successfully!!")
    return redirect('home')



def psychology(request):
    return render(request, "psychology.html")


def contact(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        desc = request.POST.get('desc')
        contact = Contact(name=name, email=email, phone=phone, desc=desc, date = datetime.today())
        contact.save()
        messages.success(request, 'Your message has been sent!!')
    return render(request, 'contactus.html')
