"use strict";
(function(){
    var instance = openerp;
    var QWeb = instance.web.qweb, _t = instance.web._t;
    
//    to bypass readonly fields in odoo
    instance.web.FormView.include({
    _process_save: function(save_obj) {
        var self = this;
        var prepend_on_create = save_obj.prepend_on_create;
        try {
            var form_invalid = false,
                values = {},
                first_invalid_field = null,
                readonly_values = {};
            for (var f in self.fields) {
                if (!self.fields.hasOwnProperty(f)) { continue; }
                f = self.fields[f];
                if (!f.is_valid()) {
                    form_invalid = true;
                    if (!first_invalid_field) {
                        first_invalid_field = f;
                    }
                } else if (f.name !== 'id' && (!self.datarecord.id || f._dirty_flag)) {
                    // Special case 'id' field, do not save this field
                    // on 'create' : save all non readonly fields
                    // on 'edit' : save non readonly modified fields
                    if (!f.get("readonly")) {
                        values[f.name] = f.get_value();
                    } else {
                        values[f.name] = f.get_value();
//                        actual code replaced with above patch
//                        readonly_values[f.name] = f.get_value();
                    }
                }
            }
            // Heuristic to assign a proper sequence number for new records that
            // are added in a dataset containing other lines with existing sequence numbers
            if (!self.datarecord.id && self.fields.sequence &&
                !_.has(values, 'sequence') && !_.isEmpty(self.dataset.cache)) {
                // Find current max or min sequence (editable top/bottom)
                var current = _[prepend_on_create ? "min" : "max"](
                    _.map(self.dataset.cache, function(o){return o.values.sequence})
                );
                values['sequence'] = prepend_on_create ? current - 1 : current + 1;
            }
            if (form_invalid) {
                self.set({'display_invalid_fields': true});
                first_invalid_field.focus();
                self.on_invalid();
                return $.Deferred().reject();
            } else {
                self.set({'display_invalid_fields': false});
                var save_deferral;
                if (!self.datarecord.id) {
                    // Creation save
                    save_deferral = self.dataset.create(values, {readonly_fields: readonly_values}).then(function(r) {
                        return self.record_created(r, prepend_on_create);
                    }, null);
                } else if (_.isEmpty(values)) {
                    // Not dirty, noop save
                    save_deferral = $.Deferred().resolve({}).promise();
                } else {
                    // Write save
                    save_deferral = self.dataset.write(self.datarecord.id, values, {readonly_fields: readonly_values}).then(function(r) {
                        return self.record_saved(r);
                    }, null);
                }
                return save_deferral;
            }
        } catch (e) {
            console.error(e);
            return $.Deferred().reject();
        }
    },
 })

    instance.web_readonly_bypass = {
        /**
         * ignore readonly: place options['readonly_fields'] into the data
         * if nothing is specified into the context
         *
         * create mode: remove read-only keys having a 'false' value
         *
         * @param {Object} data field values to possibly be updated
         * @param {Object} options Dictionary that can contain the following keys:
         *   - readonly_fields: Values from readonly fields to merge into the data object
         * @param boolean mode: True case of create, false case of write
         * @param {Object} context->readonly_by_pass
         */
        ignore_readonly: function(data, options, mode, context){
            var readonly_by_pass_fields = this.retrieve_readonly_by_pass_fields(
                options, context);
            if(mode){
                $.each( readonly_by_pass_fields, function( key, value ) {
                    if(value==false){
                        delete(readonly_by_pass_fields[key]);
                    }
                });
            }
            data = $.extend(data,readonly_by_pass_fields);
        },

        /**
         * retrieve_readonly_by_pass_fields: retrieve readonly fields to save
         * according context.
         *
         * @param {Object} options Dictionary that can contain the following keys:
         *   - readonly_fields: all values from readonly fields
         * @param {Object} context->readonly_by_pass: Can be true if all
         *   all readonly fields should be saved or an array of field name to
         *   save ie: ['readonly_field_1', 'readonly_field_2']
         * @returns {Object}: readonly key/value fields to save according context
         */
        retrieve_readonly_by_pass_fields: function(options, context){
            console.log('ksdjcfhdsjkcfhjksfc--------------',options,context);
            var readonly_by_pass_fields = {};
            if (options && 'readonly_fields' in options &&
               options['readonly_fields'] && context &&
               'readonly_by_pass' in context && context['readonly_by_pass']){
                if (_.isArray(context['readonly_by_pass'])){
                    $.each( options.readonly_fields, function( key, value ) {
                        if(_.contains(context['readonly_by_pass'], key)){
                            readonly_by_pass_fields[key] = value;
                        }
                    });
                }else{
                    readonly_by_pass_fields = options.readonly_fields;
                }
            }
            return readonly_by_pass_fields;
        },
    };

    var readonly_bypass = instance.web_readonly_bypass;

    instance.web.BufferedDataSet.include({

        init : function() {
            this._super.apply(this, arguments);
        },
        /**
         * Creates Overriding
         *
         * @param {Object} data field values to set on the new record
         * @param {Object} options Dictionary that can contain the following keys:
         *   - readonly_fields: Values from readonly fields that were updated by
         *     on_changes. Only used by the BufferedDataSet to make the o2m work correctly.
         * @returns super {$.Deferred}
         */
        create : function(data, options) {
            var self = this;
            var context = instance.web.pyeval.eval('contexts',
                                                   self.context.__eval_context);
            readonly_bypass.ignore_readonly(data, options, true, context);
            return self._super(data,options);
        },
        /**
         * Creates Overriding
         *
         * @param {Object} data field values to set on the new record
         * @param {Object} options Dictionary that can contain the following keys:
         *   - readonly_fields: Values from readonly fields that were updated by
         *     on_changes. Only used by the BufferedDataSet to make the o2m work correctly.
         * @returns super {$.Deferred}
         */
        write : function(id, data, options) {
            var self = this;
            var context = instance.web.pyeval.eval('contexts',
                                                   self.context.__eval_context);
            readonly_bypass.ignore_readonly(data, options, false, context);
            return self._super(id,data,options);
        },

    });

    instance.web.DataSet.include({
        /*
        BufferedDataSet: case of 'add an item' into a form view
        */
        init : function() {
            this._super.apply(this, arguments);
        },
        /**
         * Creates Overriding
         *
         * @param {Object} data field values to set on the new record
         * @param {Object} options Dictionary that can contain the following keys:
         *   - readonly_fields: Values from readonly fields that were updated by
         *     on_changes. Only used by the BufferedDataSet to make the o2m work correctly.
         * @returns super {$.Deferred}
         */
        create : function(data, options) {
            var self = this;
            readonly_bypass.ignore_readonly(data, options, true, self.context);
            return self._super(data,options);
        },
        /**
         * Creates Overriding
         *
         * @param {Object} data field values to set on the new record
         * @param {Object} options Dictionary that can contain the following keys:
         *   - readonly_fields: Values from readonly fields that were updated by
         *     on_changes. Only used by the BufferedDataSet to make the o2m work correctly.
         * @returns super {$.Deferred}
         */
        write : function(id, data, options) {
            var self = this;
            readonly_bypass.ignore_readonly(data, options, false, self.context);
            return self._super(id,data,options);
        },

    });

    instance.web.ProxyDataSet.include({
        /*
        ProxyDataSet: case of 'pop-up'
        */
        init : function() {
            this._super.apply(this, arguments);
        },
        /**
         * Creates Overriding
         *
         * @param {Object} data field values to set on the new record
         * @param {Object} options Dictionary that can contain the following keys:
         *   - readonly_fields: Values from readonly fields that were updated by
         *     on_changes. Only used by the BufferedDataSet to make the o2m work correctly.
         * @returns super {$.Deferred}
         */
        create : function(data, options) {
            var self = this;
            var context = instance.web.pyeval.eval('contexts',
                    self.context.__eval_context);
            readonly_bypass.ignore_readonly(data, options, true, context);
            return self._super(data,options);
        },
        /**
         * Creates Overriding
         *
         * @param {Object} data field values to set on the new record
         * @param {Object} options Dictionary that can contain the following keys:
         *   - readonly_fields: Values from readonly fields that were updated by
         *     on_changes. Only used by the BufferedDataSet to make the o2m work correctly.
         * @returns super {$.Deferred}
         */
        write : function(id, data, options) {
            var self = this;
            var context = instance.web.pyeval.eval('contexts',
                    self.context.__eval_context);
            readonly_bypass.ignore_readonly(data, options, false, context);
            return self._super(id,data,options);
        },

    });

})();
