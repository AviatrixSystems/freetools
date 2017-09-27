from constants import Cloud, SAVE_INFLUX_URL, GET_INFLUX_URL
from datetime import datetime
from fpdf import FPDF, HTMLMixin
from email_lib import send_mail
import os


class MyFPDF(FPDF, HTMLMixin):
    pass


def get_letency_throughput(cloud_id, source_region, destination_regions, timestamp, influx_db_client):
    """
    This functions defines that it get the latency and throughput from influxdb for specific timeseries and
    destination cloud regions
    :param cloud_id: cloud id
    :param source_region: name of source region
    :param destination_regions: list of destination cloud regions
    :param timestamp: timestamp renge
    :param influx_db_client:
    :return: return resultset
    """
    measurement = Cloud(int(cloud_id)).name
    if timestamp in ['12h', '1d']:
        query = "select * from %s where source_region='%s' AND" % (measurement, source_region)
        if destination_regions:
            for index, destination_region in enumerate(destination_regions):
                if index == 0:
                    query += " (destination_region='%s'" % destination_region
                else:
                    query += " OR destination_region='%s'" % destination_region
        query += ')'
        if timestamp:
            query += ' AND time > now() - %s' % timestamp

        responce = influx_db_client.query(query)
        print type(responce)
        if responce.error:
            raise Exception('Internal server error')
        result = convert_to_speedtest_format(responce.raw)
    elif timestamp in ['7d', '15d', '30d']:
        result = {'data': []}
        for destination_region in destination_regions:
            query = "select mean(latency), mean(throughput) from %s where source_region='%s' AND " \
                    "destination_region='%s' and time > now() - %s group by time(1d)" % \
                    (measurement, source_region, destination_region, timestamp)
            responce = influx_db_client.query(query)
            formatted_data = convert_to_speedtest_for_day_format(responce.raw, source_region, destination_region)
            if formatted_data:
                result['data'] += formatted_data
    return result


def save_letency_throughput(data, influx_db_client):
    """
    This function defines that store the data into influxDB
    :param cloud_id: cloud id
    :param source_region: name of source region
    :return: None
    """
    current_datetime_millis = long((datetime.utcnow() - datetime.utcnow().utcfromtimestamp(0)).total_seconds() * 1000.0)
    set_timestamp_in_data(data, current_datetime_millis)
    influx_db_client.write_points(data, time_precision='ms')


def set_timestamp_in_data(points, current_datetime_millis):
    """
    This function defines that set timestamp in data
    :param points: list of data
    :param current_datetime_millis: timestamp in miliseconds
    :return: None
    """
    for point in points:
        point['time'] = current_datetime_millis


def convert_to_speedtest_for_day_format(responce, source_region, destination_region):
    """
    This function defines that convert responce in latency and throughput
    :param responce: responce data
    :param source_region: name of source region
    :param destination_region: name of destination region
    :return: List of latency and throughput data
    """
    data = responce['series'][0]
    result = []
    for value in data['values']:
        if not value[1] or not value[2]:
            continue
        region = {}
        region['source_region'] = source_region
        region['destination_region'] = destination_region
        region['latency'] = value[1]
        region['throughput'] = value[2]
        region['time'] = value[0]
        result.append(region)

    return result


def convert_to_speedtest_format(responce):
    """
    This function defines that format the responce into latency and throughput format
    :param responce: resultset of influxDB
    :return: formatted result
    """
    data = responce['series'][0]
    columns = data['columns']
    result = {'data': []}
    for value in data['values']:
        region = {}
        for index, column in enumerate(columns):
            region[column] = value[index]
        if region:
            result['data'].append(region)
    return result


def generate_pdf_send_mail(email_id, source_cloud_provider, source_region, latency):
    try:
        os.mkdir(email_id)
    except:
        pass
    pdf_path = '%s/result.pdf' % email_id
    pdf = MyFPDF()
    # First page
    content = generate_pdf(source_cloud_provider, source_region, latency)
    pdf.add_page()
    pdf.write_html(content)
    pdf.output(pdf_path, 'F')
    send_mail('ramesh.tathe@opcito.com', [email_id], 'Test performance result', 'Hello,\n\nPlease find test performance result in attachment.\n\nThanks\nAviatrix Team', files=[pdf_path])



def generate_pdf(source_cloud_provider, user_location, latency):
    content = '<H1 align="center">Aviatrix</H1><table border="1" width="50%">' \
              '<thead><tr><th width="40%">Source Cloud</th><th width="60%">' \
              'User Location</th></tr></thead><tbody><tr><td>' + \
              source_cloud_provider + '</td><td>' + user_location + '</td>' \
              '</tr></tbody></table><table border="1" width="50%"><thead>' \
              '<tr><th width="70%">Region</th><th width="30%">Latency</th>' \
            '</tr></thead><tbody>'
    for region_ob in latency:
        content += "<tr><td>%s</td><td>%s</td></tr>" % \
                   (region_ob['label'], region_ob['latency'])
    content += "</tbody></table>"
    return content
