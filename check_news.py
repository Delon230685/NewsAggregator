import requests

response = requests.get('http://localhost:8000/api/news/')
news = response.json()

print(f'Найдено новостей: {len(news)}')
print('='*50)

for i, n in enumerate(news[:5], 1):
    print(f'{i}. {n["title"]}')
    print(f'   ID: {n["id"]}')
    print()