<template>
    <div>
        <b-tabs v-if="reports">
            <b-tab v-for="report in reports" :key="report.source" v-show="reports.messages">
                <template v-slot:title>{{report.source}}</template>
                <b-table :items="report.messages">
                    <template v-slot:cell(Message)="data">
                        <span v-html="data.value"></span>
                    </template>
                </b-table>
            </b-tab>
        </b-tabs>
    </div>
</template>

<script>
    export default {
        name: "Report",
        props: {
            reports: Array
        }
    }
</script>

<style scoped>

</style>