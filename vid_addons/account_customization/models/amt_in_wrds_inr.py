# -*- coding: utf-8 -*-
# Part of Openerp. See LICENSE file for full copyright and licensing details.

import logging
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

#-------------------------------------------------------------
#ENGLISH
#-------------------------------------------------------------

to_19 = ( 'Zero',  'One',   'Two',  'Three', 'Four',   'Five',   'Six',
          'Seven', 'Eight', 'Nine', 'Ten',   'Eleven', 'Twelve', 'Thirteen',
          'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen' )
tens  = ( 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety')
denom = ( '',  'Lakh',         'Crore',       'Arab',       'Thousand Crore',
          'Lakh Crore',  'Crore Crore',)

def _convert_nn(val):
    """convert a value < 100 to English.
    """
    if val < 20:
        return to_19[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens)):
        if dval + 10 > val:
            if val % 10:
                return dcap + '-' + to_19[val % 10]
            return dcap

def _convert_nnn(val):
    """
        convert a value < 1000 to english, special cased because it is the level that kicks 
        off the < 100 special case.  The rest are more general.  This also allows you to
        get strings in the form of 'forty-five hundred' if called directly.
    """
    word = ''
    (mod, rem) = (val % 100, val // 100)
    if rem > 0:
        word = to_19[rem] + ' Hundred'
        if mod > 0:
            word += ' '
    if mod > 0:
        word += _convert_nn(mod)
    return word

def _convert_nnnn(val):
    """
        convert a value < 100000 to english, special cased because it is the level that kicks 
        off the < 100 special case.  The rest are more general.  This also allows you to
        get strings in the form of 'forty-five hundred' if called directly.
    """
    word = ''
    (mod, rem) = (val % 1000, val // 1000)
    if rem > 0:
        word = _convert_nn(rem) + ' Thousand ,'
        if mod > 0:
            word += ' '
    if mod > 0:
        word += _convert_nnn(mod)
    return word

def _convert_nnnnn(val):
    """
        convert a value < 100000 to english, special cased because it is the level that kicks 
        off the < 100 special case.  The rest are more general.  This also allows you to
        get strings in the form of 'forty-five hundred' if called directly.
    """
    word = ''
    (mod, rem) = (val % 100000, val // 100000)
    if rem > 0:
        word = _convert_nn(rem) + ' Lakh ,'
        if mod > 0:
            word += ' '
    if mod > 0:
        word += _convert_nnnn(mod)
    return word
def _convert_nnnnnn(val):
    """
        convert a value < 100000 to english, special cased because it is the level that kicks 
        off the < 100 special case.  The rest are more general.  This also allows you to
        get strings in the form of 'forty-five hundred' if called directly.
    """
    word = ''
    (mod, rem) = (val % 10000000, val // 10000000)
    if rem > 0:
        word = _convert_nn(rem) + ' Crore ,'
        if mod > 0:
            word += ' '
    if mod > 0:
        word += _convert_nnnnn(mod)
    return word

def english_number(val):
    if val < 100:
        return _convert_nn(val)
    if val < 1000:
        return _convert_nnn(val)
    if val < 100000:
        return _convert_nnnn(val)
    if val < 10000000:
        return _convert_nnnnn(val)
    if val < 1000000000:
        return _convert_nnnnnn(val)

def amount_to_text(number, currency):
    number = '%.2f' % number
    units_name = currency
    list = str(number).split('.')
    paise_name,end_word='',''
    start_word = english_number(int(list[0]))
    paise_number = int(list[1])
    if paise_number>0:
        end_word = english_number(int(list[1]))
        paise_name = (paise_number > 1) and 'Paise' or 'Paisa'

    return ' '.join(filter(None, [units_name, start_word, (start_word or units_name) and (end_word or paise_name) and 'and', end_word, paise_name]))


#-------------------------------------------------------------
# Generic functions
#-------------------------------------------------------------

_translate_funcs = {'en' : amount_to_text}
    
#TODO: we should use the country AND language (ex: septante VS soixante dix)
#TODO: we should use en by default, but the translation func is yet to be implemented
def amount_to_text(nbr, lang='en', currency='INR'):
    """ Converts an integer to its textual representation, using the language set in the context if any.
    
        Example::
        
            1654: thousands six cent cinquante-quatre.
    """
    import openerp.loglevels as loglevels
#    if nbr > 10000000:
#        _logger.warning(_("Number too large '%d', can not translate it"))
#        return str(nbr)
    
    if not _translate_funcs.has_key(lang):
        _logger.warning(_("no translation function found for lang: '%s'"), lang)
        #TODO: (default should be en) same as above
        lang = 'en'
    return _translate_funcs[lang](abs(nbr), currency)

if __name__=='__main__':
    from sys import argv
    
    lang = 'nl'
    if len(argv) < 2:
        for i in range(1,200):
            print i, ">>", int_to_text(i, lang)
        for i in range(200,999999,139):
            print i, ">>", int_to_text(i, lang)
    else:
        print int_to_text(int(argv[1]), lang)