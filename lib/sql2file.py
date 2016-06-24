#!/usr/bin/python
"""
Created on Tue Apr 29 09:25:43 2014
@author: mints
"""
import argparse
from astropy.io.votable.tree import VOTableFile, Resource, Table, Field
from astropy.table import Table as ATable
from lib.sqlconnection import SQLConnection
import os
import errno

LOCAL_CONN = SQLConnection('xmn')


def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise  # re-raise exception if a different error occured


def get_vo_type(oid):
    """
    Convert PostgreSQL type oid to VO type.
    """
    typename = LOCAL_CONN.exec_return("""select typname
                                           from pg_type
                                          where oid = %s""" % oid)
    if typename == 'bool':
        return 'boolean'
    if typename == 'char':
        return typename
    elif typename in ['int2', 'int4', 'int8']:
        return 'int'
    elif typename in ['float4', 'float8']:
        return 'float'
    elif typename == 'varchar':
        return 'char'
    else:
        return None


def get_astropy_type(oid, size):
    """
    Convert AstroPy type oid to VO type.
    """
    typename = LOCAL_CONN.exec_return("""select typname
                                           from pg_type
                                          where oid = %s""" % oid)
    if typename == 'bool':
        return 'bool'
    elif typename in ['char', 'varchar']:
        if size is not None:
            return 'S%s' % size
        else:
            return 'S'
    elif typename in ['int2', 'int4', 'int8', 'float4', 'float8']:
        return '%s%s' % (typename[0], typename[-1])
    else:
        return None


def sql_to_vo(sql, output_name=None):
    """
    Run SQL query and save output to VO table.
    """
    data = LOCAL_CONN.execute_set(sql, False)
    # Create a new VOTable file...
    votable = VOTableFile()
    # ...with one resource...
    resource = Resource()
    votable.resources.append(resource)
    # ... with one table
    table = Table(votable)
    resource.tables.append(table)
    for column_descr in LOCAL_CONN.last_description:
        # Define fields
        xtype = get_vo_type(column_descr.type_code)
        if xtype == 'char':
            table.fields.extend([
                Field(votable,
                      name=column_descr.name,
                      datatype=xtype,
                      arraysize=str(column_descr.internal_size))])
        else:
            table.fields.extend([Field(votable,
                                       name=column_descr.name,
                                       datatype=xtype)])
    table.create_arrays(len(data))
    for irow, row in enumerate(data):
        table.array[irow] = row
    if output_name is not None:
        # Save to file
        votable.to_xml(output_name)
        return True
    else:
        # Return VOTable
        return votable


def create_sqlite_database(tablename, columnnames, datatypes):
    import sqlite3
    fileconn = sqlite3.connect('%s.sqlite' % tablename)
    create_lines = ['%s %s' % (columnnames[i],
                               datatypes[i]) for i in xrange(len(columnnames))]
    sqlite_create = 'create table %s (%s);' % (tablename,
                                               ','.join(create_lines))
    fileconn.cursor().execute(sqlite_create)
    fileconn.commit()
    return fileconn


def sql_to_file(sql, output_name=None, write_format='ascii',
                connection=LOCAL_CONN, automatic_extention=True,
                overwrite=False, append=False):
    """
    Run SQL query and save output to ascii (or other formats) file.
    """
    data = connection.exec_return(sql, False, return_all=True)
    column_names = []
    column_types = []
    for column_descr in connection.last_description:
        column_names.append(column_descr.name)
        column_types.append(get_astropy_type(column_descr.type_code,
                                             column_descr.internal_size))

    format_list = write_format.split(',')
    if 'sqlite' in format_list:
        import sqlite3
        if output_name is None:
            output_name = ':memory:'
        if overwrite:
            silentremove('%s.sqlite' % output_name)
        if not append:
            sqlite_table = create_sqlite_database(output_name,
                                                  column_names, column_types)
        else:
            sqlite_table = sqlite3.connect('%s.sqlite' % output_name)
    if len(data) == 0:
        table = ATable(names=column_names, dtype=column_types)
    else:
        table = ATable(data=zip(*data), names=column_names, dtype=column_types)
    if output_name is None:
        return table
    else:
        for single_write_format in format_list:
            if single_write_format == 'sqlite':
                insert = 'INSERT INTO %s VALUES (%s)' % (output_name,
                                                         ','.join('?'*len(column_names)))
                sqlite_table.executemany(insert, data)
                sqlite_table.commit()
                sqlite_table.close()
            else:
                if automatic_extention or len(format_list) > 1:
                    file_name = '%s.%s' % (output_name, single_write_format)
                else:
                    file_name = output_name
                if overwrite:
                    silentremove(file_name)
                table.write(file_name, format=single_write_format)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="""Save SQL output as VOTable""",
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-o', '--output', type=str, default=None,
                        help='Output file')

    parser.add_argument('-f', '--input', type=str, default=None,
                        help='Input SQL file')

    parser.add_argument('-e', '--script', type=str, default=None,
                        help='SQL script')

    args = parser.parse_args()
    if args.script is not None:
        script = args.script
    else:
        script = ' '.join(open(args.input, 'r').readlines())
    sql_to_file(script, args.output, 'votable')
    #sql_to_file(script, args.output, 'sqlite')
