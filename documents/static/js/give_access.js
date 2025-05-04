$(document).ready(function() {
    const userSearchUrl = '/documents/user-search/';
    $('.user-select').select2({
        ajax: {
            url: userSearchUrl,
            dataType: 'json',
            delay: 250,
            data: function(params) {
                return {
                    q: params.term,
                    page: params.page
                };
            },
            processResults: function(data, params) {
                params.page = params.page || 1;
                return {
                    results: data.results,
                    pagination: {
                        more: data.pagination.more
                    }
                };
            },
            cache: true
        },
        minimumInputLength: 1,
        placeholder: 'Начните вводить имя или email',
        language: {
            noResults: function() {
                return "<i class='fas fa-search'></i> Пользователи не найдены";
            }
        },
        templateResult: function(user) {
            if (user.loading) return user.text;
            return $('<span>').html(
                `<i class="fas fa-user"></i> ${user.text}`
            );
        }
    });
});
