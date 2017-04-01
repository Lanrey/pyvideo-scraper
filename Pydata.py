from multiprocessing.pool import ThreadPool as Pool
import requests
import bs4
import argparse


root_url = 'http://pyvideo.org'
index_url = root_url + '/events/pydata.html'


def get_video_url():

    response = requests.get(index_url)

    soup = bs4.BeautifulSoup(response.text, "lxml")

    return [a.attrs.get('href') for a in soup.select('h4.entry-title a[href]')]


def get_video_data(get_video_url):

    video_data = {}
    response = requests.get(root_url + get_video_url)
    soup = bs4.BeautifulSoup(response.text, "lxml")

    video_data['title'] = soup.select('h2.entry-title a[href]')[0].get_text().strip(" \n")
    video_data['speakers'] = soup.address.a.get_text()
    video_data['views'] = 0
    video_data['likes'] = 0
    video_data['dislikes'] = 0

    try:
        video_data['video_url'] = [a.attrs.get('href')for a in soup.select('div.details-content'
                                                                           ' a[href^=http://www.youtube.com]')]

        video_string = ''.join(video_data['video_url'])
        response2 = requests.get(video_string)
        soup2 = bs4.BeautifulSoup(response2.text, "lxml")

        video_data['views'] = soup2.select('div.watch-view-count')[0].get_text().split(" ")[0]

        strip_like_section = soup2.find('button', title='I like this')
        video_data['likes'] = strip_like_section.select('span.yt-uix-button-content')[0].get_text()

        strip_dislike_section = soup2.find('button', title='I dislike this')
        video_data['dislikes'] = strip_dislike_section.select('span.yt-uix-button-content')[0].get_text()

    except:
        pass
    return video_data


def parse_args():
    parser = argparse.ArgumentParser(description='Show PyData video statistics.')
    parser.add_argument('--sort', metavar='FIELD', choices=['views', 'likes', 'dislikes'],
                        default='views',
                        help='sort by the specified field. Options are views, likes and dislikes.')
    parser.add_argument('--max', metavar='MAX', type=int, help='show the top MAX entries only.')
    parser.add_argument('--csv', action='store_true', default=False,
                        help='output the data in CSV format.')
    parser.add_argument('--workers', type=int, default=8,
                        help='number of workers to use, 8 by default.')
    return parser.parse_args()


def show_video_stats(options):

    pool = Pool(options.workers)
    video_page_urls = get_video_url()
    results = sorted(pool.map(get_video_data, video_page_urls), key=lambda video: video[options.sort],
                     reverse=True)
    #print(len(results))

    max = options.max
    if max is None or max > len(results):
        max = len(results)
    if options.csv:
        print(u'"title","speakers", "views","likes","dislikes"')
    else:
        print(u'Views  +1  -1 Title (Speakers)')
    for i in range(max):
        if options.csv:
            print(u'"{0}","{1}",{2},{3},{4}'.format(
                results[i]['title'], results[i]['speakers'], results[i]['views'],
                results[i]['likes'], results[i]['dislikes']))
        else:
            print(u'{0} {1} {2} {3} ({4})'.format(
                results[i]['views'], results[i]['likes'], results[i]['dislikes'], results[i]['title'],
                results[i]['speakers']))

if __name__ == '__main__':
    show_video_stats(parse_args())
