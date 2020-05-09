<template>
    <div>
        <b-button-group class="mx-1 my-2">
            <b-button @click="update">update</b-button>
            <b-button @click="$emit('add_node')">Add</b-button>
            <b-button @click="$emit('delete_node')">Delete</b-button>
        </b-button-group>
        <SlVueTree v-model="nodes" v-on:nodeclick="nodeChange($event)"></SlVueTree>
    </div>
</template>

<script>
    import SlVueTree from 'sl-vue-tree';
    import 'sl-vue-tree/dist/sl-vue-tree-minimal.css';

    export default {
        name: "TreeView",
        components: { SlVueTree },
        data: function() {
            return {
                nodes: []
            }
        },
        props: {
            config: Object
        },
        methods: {
            update() {
                //this.$parent.update();
                this.$emit("update_config")
            },
            nodeChange(node) {
                this.$parent.updateCurrentNode(node.data);
            },
            extract_tree_data(trees) {
                var tree_data = [];
                for (let i = 0; i < trees.length; i++) {
                    var node = trees[i];
                    tree_data.push({'title': node.title, 'data': node, 'children': this.extract_tree_data(node.children)});
                }
                return tree_data
            }
        },
        watch: {
            config: function() {
                this.nodes = this.extract_tree_data(this.config.log_trees)
            }
        },
    }
</script>

<style scoped>

</style>