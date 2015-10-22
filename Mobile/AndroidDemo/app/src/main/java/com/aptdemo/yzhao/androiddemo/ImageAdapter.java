package com.aptdemo.yzhao.androiddemo;


import android.widget.BaseAdapter;
import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.GridView;
import com.squareup.picasso.Picasso;

import java.util.ArrayList;

public class ImageAdapter extends BaseAdapter {
    private Context mContext;
    private ArrayList<String> imageURLs;

    public ImageAdapter(Context c, ArrayList<String> imageURLs) {
        mContext = c;
        this.imageURLs = imageURLs;
    }

    public int getCount() {
        return imageURLs.size();
    }

    public Object getItem(int position) {
        return null;
    }

    public long getItemId(int position) {
        return 0;
    }

    // create a new ImageView for each item referenced by the Adapter
    public View getView(int position, View convertView, ViewGroup parent) {
        ImageView imageView;
        if (convertView == null) {  // if it's not recycled, initialize some attributes
            imageView = new ImageView(mContext);
            imageView.setLayoutParams(new GridView.LayoutParams(250, 250));
            imageView.setScaleType(ImageView.ScaleType.CENTER_CROP);
        } else {
            imageView = (ImageView) convertView;
        }

        Picasso.with(mContext).load(imageURLs.get(position)).into(imageView);
        return imageView;
    }

}