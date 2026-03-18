"""
Email templates for Rocket Logistic contact form
Supports English and Bulgarian languages
"""
import html

def get_company_notification_template(data, language='en'):
    """
    Generate email template for company notification

    Args:
        data: dict with keys: name, email, phone, message, timestamp
        language: 'en' or 'bg'

    Returns:
        tuple: (subject, html_body)
    """
    name = html.escape(data['name'])
    email = html.escape(data['email'])
    phone = html.escape(data.get('phone') or '')
    message = html.escape(data['message'])
    load_date = html.escape(data.get('load_date') or '')
    date_flexibility = data.get('date_flexibility') or ''

    if language == 'bg':
        subject = f"Ново запитване от {name}"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1E3A5F; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f5f5f5; padding: 30px; }}
                .field {{ margin-bottom: 20px; }}
                .label {{ font-weight: bold; color: #1E3A5F; }}
                .value {{ margin-top: 5px; padding: 10px; background-color: white; border-left: 3px solid #FF6B35; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Ново запитване от уебсайта</h1>
                </div>
                <div class="content">
                    <p>Получихте ново запитване от уебсайта на Rocket Logistic:</p>

                    <div class="field">
                        <div class="label">Име:</div>
                        <div class="value">{name}</div>
                    </div>

                    <div class="field">
                        <div class="label">Имейл:</div>
                        <div class="value"><a href="mailto:{email}">{email}</a></div>
                    </div>

                    <div class="field">
                        <div class="label">Телефон:</div>
                        <div class="value">{phone if phone else 'Не е посочен'}</div>
                    </div>

                    <div class="field">
                        <div class="label">Съобщение:</div>
                        <div class="value">{message}</div>
                    </div>

                    <div class="field">
                        <div class="label">Предпочитана дата на товарене:</div>
                        <div class="value">{load_date if load_date else 'Не е посочена'}</div>
                    </div>

                    <div class="field">
                        <div class="label">Гъвкавост на датата:</div>
                        <div class="value">{'Гъвкава / Договаряема' if date_flexibility == 'flexible' else 'Фиксирана / Трябва да е точна' if date_flexibility == 'fixed' else 'Не е посочена'}</div>
                    </div>

                    <div class="field">
                        <div class="label">Дата и час:</div>
                        <div class="value">{data['timestamp']}</div>
                    </div>
                </div>
                <div class="footer">
                    <p>Това съобщение е генерирано автоматично от контактната форма на Rocket Logistic</p>
                </div>
            </div>
        </body>
        </html>
        """
    else:  # English
        subject = f"New inquiry from {name}"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1E3A5F; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f5f5f5; padding: 30px; }}
                .field {{ margin-bottom: 20px; }}
                .label {{ font-weight: bold; color: #1E3A5F; }}
                .value {{ margin-top: 5px; padding: 10px; background-color: white; border-left: 3px solid #FF6B35; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New Website Inquiry</h1>
                </div>
                <div class="content">
                    <p>You have received a new inquiry from the Rocket Logistic website:</p>

                    <div class="field">
                        <div class="label">Name:</div>
                        <div class="value">{name}</div>
                    </div>

                    <div class="field">
                        <div class="label">Email:</div>
                        <div class="value"><a href="mailto:{email}">{email}</a></div>
                    </div>

                    <div class="field">
                        <div class="label">Phone:</div>
                        <div class="value">{phone if phone else 'Not provided'}</div>
                    </div>

                    <div class="field">
                        <div class="label">Message:</div>
                        <div class="value">{message}</div>
                    </div>

                    <div class="field">
                        <div class="label">Preferred Load Date:</div>
                        <div class="value">{load_date if load_date else 'Not provided'}</div>
                    </div>

                    <div class="field">
                        <div class="label">Date Flexibility:</div>
                        <div class="value">{'Flexible / Negotiable' if date_flexibility == 'flexible' else 'Fixed / Must be exact' if date_flexibility == 'fixed' else 'Not provided'}</div>
                    </div>

                    <div class="field">
                        <div class="label">Date & Time:</div>
                        <div class="value">{data['timestamp']}</div>
                    </div>
                </div>
                <div class="footer">
                    <p>This message was automatically generated from the Rocket Logistic contact form</p>
                </div>
            </div>
        </body>
        </html>
        """

    return subject, html_body


def get_customer_confirmation_template(data, language='en'):
    """
    Generate email template for customer confirmation

    Args:
        data: dict with keys: name, email
        language: 'en' or 'bg'

    Returns:
        tuple: (subject, html_body)
    """
    name = html.escape(data['name'])

    if language == 'bg':
        subject = "Благодарим за вашето запитване - Rocket Logistic"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1E3A5F; color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f5f5f5; }}
                .message {{ background-color: white; padding: 20px; border-left: 4px solid #FF6B35; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                .cta {{ text-align: center; margin: 30px 0; }}
                .button {{ display: inline-block; padding: 12px 30px; background-color: #FF6B35; color: white; text-decoration: none; border-radius: 4px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Rocket Logistic</h1>
                    <p>Вашият надежден партньор</p>
                </div>
                <div class="content">
                    <h2>Здравейте, {name}!</h2>

                    <div class="message">
                        <p>Благодарим ви, че се свързахте с Rocket Logistic!</p>
                        <p>Получихме вашето съобщение и ще се свържем с вас възможно най-скоро. Нашият екип обикновено отговаря в рамките на 24 часа през работни дни.</p>
                    </div>

                    <p>Междувременно можете да:</p>
                    <ul>
                        <li>Разгледате нашите <a href="#services">услуги</a></li>
                        <li>Научете повече <a href="#about">за нас</a></li>
                        <li>Свържете се с нас директно на <a href="tel:+35928123456">+359 2 812 3456</a></li>
                    </ul>

                    <div class="cta">
                        <a href="mailto:office@r-logistic.com" class="button">Свържете се с нас</a>
                    </div>
                </div>
                <div class="footer">
                    <p><strong>Rocket Logistic</strong></p>
                    <p>бул. "Цариградско шосе" 115, София 1784, България</p>
                    <p>Телефон: +359 2 812 3456 | Email: office@r-logistic.com</p>
                </div>
            </div>
        </body>
        </html>
        """
    else:  # English
        subject = "Thank you for your inquiry - Rocket Logistic"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1E3A5F; color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f5f5f5; }}
                .message {{ background-color: white; padding: 20px; border-left: 4px solid #FF6B35; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                .cta {{ text-align: center; margin: 30px 0; }}
                .button {{ display: inline-block; padding: 12px 30px; background-color: #FF6B35; color: white; text-decoration: none; border-radius: 4px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Rocket Logistic</h1>
                    <p>Your trusted freight partner</p>
                </div>
                <div class="content">
                    <h2>Hello, {name}!</h2>

                    <div class="message">
                        <p>Thank you for contacting Rocket Logistic!</p>
                        <p>We have received your message and will get back to you as soon as possible. Our team typically responds within 24 hours on business days.</p>
                    </div>

                    <p>In the meantime, feel free to:</p>
                    <ul>
                        <li>Explore our <a href="#services">services</a></li>
                        <li>Learn more <a href="#about">about us</a></li>
                        <li>Call us directly at <a href="tel:+35928123456">+359 2 812 3456</a></li>
                    </ul>

                    <div class="cta">
                        <a href="mailto:office@r-logistic.com" class="button">Contact Us</a>
                    </div>
                </div>
                <div class="footer">
                    <p><strong>Rocket Logistic</strong></p>
                    <p>115 Tsarigradsko Shose Blvd., Sofia 1784, Bulgaria</p>
                    <p>Phone: +359 2 812 3456 | Email: office@r-logistic.com</p>
                </div>
            </div>
        </body>
        </html>
        """

    return subject, html_body
