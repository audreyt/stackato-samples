require 'test_helper'

class MoviesControllerTest < ActionController::TestCase
  setup do
    @movie = movies(:one)
  end

  test "should get index" do
    get :index
    assert_response :success
    assert_not_nil assigns(:movies)
  end

  test "should get new" do
    get :new
    assert_response :success
  end

  test "should create movie" do
    assert_difference('Movie.count', 1) do
      post :create, :movie => {:title => "Boris"}
    end
    assert_redirected_to movie_path(assigns(:movie))
  end

  test "should show movie" do
    get :show, :id => @movie.to_param
    assert_response :success
  end

  test "should get edit" do
    get :edit, :id => @movie.to_param
    assert_response :success
  end

  test "should update movie" do
    put :update, :id => @movie.to_param, :movie => @movie.attributes
    assert_redirected_to movie_path(assigns(:movie))
  end

  test "should destroy movie" do
    assert_difference('Movie.count', -1) do
      delete :destroy, :id => @movie.to_param
    end

    assert_redirected_to movies_path
  end
  test "pagination" do
    Movie.delete_all
    35.times {|i| Movie.create(:title => "title #{i}")}
    get :index
    assert_tag(:tag => 'div',
               :attributes => { :class => 'pagination'})
    #assert_tag(:tag => 'span',
    #           :content => '&laquo; Previous',
    #           :attributes => { :class => 'disabled'})
    assert_tag(:tag => 'span',
               :content => '1',
               :attributes => { :class => 'current'})
    assert_tag(:tag => 'div',
               :attributes => { :class => 'pagination'},
               :child => { :tag => 'a',
                 :attributes => { :href => "/movies?page=4" },
                 :content => "4" })
  end
  
  def test_checkout_get
    get :checkout, :id => movies(:one).id
    assert_response :success
  end

  def test_checkout_put
    post :checkout, :id => movies(:one).id, :movie => {:borrower => "Fred"}
    assert_redirected_to movies_path
  end
    
end
