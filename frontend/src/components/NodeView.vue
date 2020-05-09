<template>
    <div>
        <h2>{{ title }}</h2>
        <b-form @submit.prevent="" @reset="onReset">
            <b-form-group
                    id="name-input-group"
                    label="Name:"
                    label-for="name-input"
                    label-align="left"
                    label-size="lg"
                    align="left"
            >
                <b-form-input
                        id="name-input"
                        v-model="nodeForm.title"
                        type="text"
                        required
                        placeholder="Enter Name"
                ></b-form-input>
            </b-form-group>

            <b-form-group
                    id="description-input-group"
                    label="Description:"
                    label-for="description-input"
                    label-align="left"
                    label-size="lg"
                    align="left"
            >
                <b-form-textarea
                        id="description-input"
                        v-model="nodeForm.description"
                        placeholder="Enter description"
                ></b-form-textarea>
            </b-form-group>

            <div class="form-segment p-2 my-3">
                <b-form-group
                    id="filters-input-group"
                    label="Filters:"
                    label-align="left"
                    label-size="lg"
                    align="left"
            >
                <b-input-group v-for="(filter, index) in nodeForm.filters" :key="index" class="my-2">
                    <template v-slot:prepend>
                        <b-form-select
                            v-model="filter.field"
                            :options="filter_fields"
                            v-on:change="reactOnUnknown($event, index)"
                        ></b-form-select>
                    </template>
                    <b-form-input
                        v-model="filter.pattern"
                        type="text"
                        placeholder="Filter rule"
                    ></b-form-input>
                    <template v-slot:append>
                        <b-button @click="removeFilter(index)" class="alert-danger">
                            X
                        </b-button>
                    </template>
                </b-input-group>
                <b-button :disabled="filter_button_disabled" @click="addFilter">add Filter</b-button>
            </b-form-group>
            </div>

            <div class="form-segment p-2 my-3">
                <b-form-group
                        id="example-input-group"
                        label="Example:"
                        label-align="left"
                        label-size="lg"
                        align="left"
                >
                    <b-input-group prepend="message" for="example-message" class="my-2">
                        <b-form-input
                                id="example-message"
                                v-model="nodeForm.example.message"
                                type="text"
                                placeholder="Message Example"
                        ></b-form-input>
                    </b-input-group>
                    <b-input-group prepend="host" for="example-host" class="my-2">
                        <b-form-input
                                id="example-host"
                                v-model="nodeForm.example.host"
                                type="text"
                                placeholder="Hostname Example"
                        ></b-form-input>
                    </b-input-group>
                    <b-input-group prepend="program" for="example-program" class="my-2">
                        <b-form-input
                                id="example-program"
                                v-model="nodeForm.example.program"
                                type="text"
                                placeholder="Program Example"
                        ></b-form-input>
                    </b-input-group>
                </b-form-group>
            </div>

            <div class="form-segment p-2 my-3">
                <b-form-group
                        id="actions-input-group"
                        label="Actions:"
                        label-align="left"
                        label-size="lg"
                        align="left"
                >
                    <b-input-group v-for="(action, index) in nodeForm.actions" :key="index" class="my-2">
                        <template v-slot:prepend>
                            <b-form-select
                                    v-model="action.action"
                                    :options="action_fields"
                            ></b-form-select>
                        </template>
                        <b-form-input v-if="action.action === 'file'"
                                      v-model="action.filepath"
                                      type="text"
                                      placeholder="Filepath"
                        ></b-form-input>
                        <b-form-input v-if="action.action === 'network'"
                                      v-model="action.host"
                                      type="text"
                                      placeholder="Host"
                        ></b-form-input>
                        <b-form-input v-if="action.action === 'network'"
                                      v-model="action.port"
                                      type="text"
                                      placeholder="Port"
                        ></b-form-input>
                        <template v-slot:append>
                            <b-button @click="nodeForm.actions.splice(index, 1)" class="alert-danger">
                                X
                            </b-button>
                        </template>
                    </b-input-group>
                    <b-button @click="addAction">add Action</b-button>
                </b-form-group>
            </div>

            <b-row align-h="between" class="p-3">
                <b-button type="reset" variant="danger">Reset</b-button>
                <b-button @click="$emit('send_node_update', nodeForm)" variant="primary">Accept</b-button>
            </b-row>
        </b-form>
    </div>
</template>

<script>
    export default {
        name: "NodeView",

        data() {
            return {
                title: 'Change Configuration',
                nodeForm: {
                    name: '',
                    description: '',
                    filters: [],
                    example: {
                        message: '',
                        host: '',
                        program: ''
                    },
                    actions: [],
                },
                filter_button_disabled: false,
                filter_fields: [
                    'message',
                    'host',
                    'program',
                    'unknown',
                ],
                action_fields: [
                    'file',
                    'network'
                ]
            }
        },

        props: {
            config: Object,
            current_node: Object,
            isAdd: {
                type: Boolean,
                default: false
            }
        },

        methods: {
            onReset() {
                if (this.isAdd || this.current_node == null) {
                    this.nodeForm = {
                        name: '',
                        description: '',
                        filters: [],
                        example: {
                            message: '',
                            host: '',
                            program: ''
                        },
                        actions: [],
                    }
                }
                else {
                    this.nodeForm = this.current_node;
                }
            },

            addFilter() {
                this.nodeForm.filters.push({field: 'message', pattern: ''});
            },

            addAction() {
                this.nodeForm.actions.push({action: 'file', filepath: ''});
            },

            removeFilter(index) {
                this.nodeForm.filters.splice(index, 1);
                this.filter_button_disabled=false
            },

            reactOnUnknown(selected, index) {
                if (selected === 'unknown') {
                    this.filter_button_disabled = true;
                    this.nodeForm.filters = this.nodeForm.filters.slice(index, index + 1);
                } else {
                    this.filter_button_disabled = false;
                }
            }
        },

        watch: {
            isAdd: function () {
                if (!this.isAdd) {
                    this.title = 'Change Configuration';
                } else {
                    this.nodeForm = {
                        name: '',
                        description: '',
                        filters: [],
                        example: {
                            message: '',
                            host: '',
                            program: ''
                        },
                        actions: [],
                    };
                    this.addFilter();
                    this.title = 'Add New';
                }
            },

            current_node: function () {
                if (!this.isAdd) {
                    this.nodeForm = this.current_node
                }
                this.filter_button_disabled = false;
            }
        }
    }
</script>

<style scoped>
    .form-segment {
        border: 1px solid #ccc;
        border-radius: 16px;
    }
</style>